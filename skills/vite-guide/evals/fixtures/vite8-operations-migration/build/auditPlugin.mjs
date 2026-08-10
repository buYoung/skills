export function auditPlugin() {
  return {
    name: 'acme-audit-manifest',
    generateBundle(_options, bundle) {
      const chunks = Object.values(bundle).filter((item) => item.type === 'chunk');
      this.emitFile({
        type: 'asset',
        fileName: 'audit-manifest.json',
        source: JSON.stringify(chunks.map(({ fileName, isEntry }) => ({ fileName, isEntry })))
      });
    }
  };
}
