// File: frontend/src/supabaseClient.js

import { createClient } from '@supabase/supabase-js'

// Ganti dengan URL dan Kunci Anon Publik Anda
const supabaseUrl = 'https://jurnaltvriberkeringat.netlify.app/'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZmbndoZHVwaGVmZWVuc2pkdHR0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE4MjU0ODMsImV4cCI6MjA2NzQwMTQ4M30.nGf-vtoc-EdwK81pBvWSOWet5hz1LV6eQU4gymfBD_I'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)