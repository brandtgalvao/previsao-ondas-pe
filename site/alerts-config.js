// Preencha com os valores do SEU projeto Supabase (Project Settings > API).
// A "anon key" e publica por design no Supabase - protegida pelas RLS
// definidas em db/schema.sql (o anon so pode inserir em "subscribers" e
// chamar a funcao "unsubscribe", nunca ler dados). NUNCA coloque aqui a
// "service_role key" - essa fica exclusivamente no secret SUPABASE_SERVICE_KEY
// do GitHub Actions, usada so pelo pipeline Python.
window.ALERTS_CONFIG = {
  supabaseUrl: "https://xkjhbxgxmskvnzbxupxr.supabase.co",
  supabaseAnonKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhramhieGd4bXNrdm56Ynh1cHhyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk4NjI4OTQsImV4cCI6MjEwNTQzODg5NH0.pB5ItdseakMvZshv_7Lu1Y0iiphRw6jobnjcyxRPUiI",
};
