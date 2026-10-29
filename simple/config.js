/* Vigi-Track Simple: where reports are saved.

   Leave both values empty: the app runs in demo mode, and reports stay in this browser only.
   Fill them in: reports go to your Supabase database and everyone sees them.

   Where to find them: Supabase dashboard > your project > Project Settings > API Keys.
   - supabaseUrl: the Project URL, like "https://abcdefgh.supabase.co"
   - supabaseKey: the "publishable" key (sb_publishable_...) or the legacy "anon" key.
   This key is made to be public. What visitors can do with it is decided by the
   rules in supabase/setup.sql (read and add reports, nothing else). */
window.VT_CONFIG = {
  supabaseUrl: "",
  supabaseKey: ""
};
