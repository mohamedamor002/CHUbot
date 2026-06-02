#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            // En production : démarre le backend comme sidecar
            #[cfg(not(debug_assertions))]
            {
                use tauri_plugin_shell::ShellExt;
                app.shell()
                    .sidecar("chubot-backend")
                    .expect("sidecar introuvable")
                    .spawn()
                    .expect("impossible de démarrer le backend");
            }

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
