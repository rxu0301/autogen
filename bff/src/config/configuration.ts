export default () => ({
  port: parseInt(process.env.PORT || '4000', 10),
  backendUrl: process.env.BACKEND_URL || 'http://localhost:8000',
});
