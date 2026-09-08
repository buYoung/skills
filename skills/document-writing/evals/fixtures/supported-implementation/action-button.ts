import tokens from './tokens.json';
export type ActionButtonProps = { label: string; tone: 'primary' | 'quiet' };
const internalPadding = 12;
export function ActionButton(props: ActionButtonProps) {
  return { label: props.label, background: props.tone === 'primary' ? tokens['action.background'] : 'transparent', padding: internalPadding };
}
