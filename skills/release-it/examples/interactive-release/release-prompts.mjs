import { confirm } from '@inquirer/prompts';
import { Plugin } from 'release-it';

export class ReleaseStopped extends Error {
  constructor(message) {
    super(message, { cause: 'INFO' });
    this.name = 'ReleaseStopped';
  }
}

export async function requireAnswer(pendingAnswer, stage) {
  try {
    return await pendingAnswer;
  } catch (error) {
    if (error instanceof Error && ['ExitPromptError', 'AbortPromptError'].includes(error.name)) {
      throw new ReleaseStopped(`Cancelled at ${stage}.`);
    }
    throw error;
  }
}

// release-it 21.0.1 calls register() and show(); there is no run() interface.
export class InquirerPrompt {
  prompts = new Map();
  completed = [];
  attempted = [];
  tagName;

  register(definitions, namespace = 'default') {
    this.prompts.set(namespace, { ...this.prompts.get(namespace), ...definitions });
  }

  async show({ enabled = true, prompt, namespace = 'default', task, context }) {
    if (!enabled) return false;
    const definition = this.prompts.get(namespace)?.[prompt];
    const expected = ['commit', 'tag', 'push'][this.completed.length];
    if (namespace !== 'git' || prompt !== expected || definition?.type !== 'confirm') {
      throw new Error(`Unsupported release prompt: ${namespace}.${prompt}`);
    }
    if (typeof task !== 'function') throw new Error(`Missing task: ${namespace}.${prompt}`);
    this.tagName = context.tagName;
    const answer = await requireAnswer(confirm({
      message: definition.message(context),
      default: false
    }), prompt);
    // Returning false would skip only this task, allowing subsequent Git steps.
    if (answer !== true) throw new ReleaseStopped(`Declined ${prompt}.`);
    this.attempted.push(prompt);
    const result = await task(answer);
    this.completed.push(prompt);
    return result;
  }
}

// Load this module as the FIRST external plugin, before any file-writing plugin.
export default class SelectedVersionGuard extends Plugin {
  beforeBump() {
    const { version, latestVersion } = this.config.getContext();
    if (version !== this.options.selectedVersion || latestVersion !== this.options.currentVersion) {
      throw new Error('Resolved version differs from the displayed selection; stopping before bump.');
    }
    if (this.config.isCI || this.config.isPromptOnlyVersion) {
      throw new Error('Interactive confirmations must remain enabled.');
    }
  }
}
