import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { describeWorkspace } from "../lib/workspace.ts";

export default function (pi: ExtensionAPI) {
  pi.registerFlag("acme-compact", {
    type: "boolean",
    description: "Show only the workspace name in Acme output",
    default: false,
  });

  pi.registerTool({
    name: "acme_workspace_info",
    label: "Acme Workspace",
    description: "Describe the current session workspace without reading its files.",
    promptSnippet: "Identify the current session workspace",
    promptGuidelines: [
      "Use acme_workspace_info when the workspace identity is needed.",
      "The result identifies the directory; it does not describe its contents.",
    ],
    parameters: Type.Object({}),
    async execute(_toolCallId, _params, signal, _onUpdate, ctx) {
      signal?.throwIfAborted();
      const details = describeWorkspace(ctx.cwd);
      const isCompact = pi.getFlag("acme-compact") === true;
      return {
        content: [{
          type: "text",
          text: isCompact ? details.name : `${details.name}\n${details.path}`,
        }],
        details,
      };
    },
  });

  pi.registerCommand("acme-info", {
    description: "Show the current workspace without calling a model",
    handler: async (_args, ctx) => {
      const details = describeWorkspace(ctx.cwd);
      const isCompact = pi.getFlag("acme-compact") === true;
      pi.sendMessage({
        customType: "acme-workspace-info",
        content: isCompact ? details.name : `${details.name}\n${details.path}`,
        details,
        display: true,
      });
    },
  });
}
