export default {
  base: '/console/',
  ssr: {
    external: ['@fixture/banner', '@fixture/theme'],
    resolve: { externalConditions: ['node', 'custom'] }
  },
  build: { sourcemap: true }
};
