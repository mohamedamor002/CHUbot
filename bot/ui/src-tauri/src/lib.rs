use std::sync::Mutex;
use tauri::Manager;
use tauri_plugin_shell::process::CommandChild;

struct BackendProcess(Mutex<Option<CommandChild>>);

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(BackendProcess(Mutex::new(None)))
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

            // En production : démarre le backend comme sidecar et garde le handle en vie
            #[cfg(not(debug_assertions))]
            {
                use tauri_plugin_shell::ShellExt;

                // Tuer tout backend résiduel pour libérer le port 8765
                let _ = std::process::Command::new("taskkill")
                    .args(["/F", "/IM", "chubot-backend.exe"])
                    .output();
                std::thread::sleep(std::time::Duration::from_millis(500));

                // Chemin absolu vers l'index vectoriel (installé à côté de l'exe)
                let vector_store_path = std::env::current_exe()
                    .ok()
                    .and_then(|p| p.parent().map(|p| p.join("data").join("indexes")))
                    .unwrap_or_else(|| std::path::PathBuf::from("./data/indexes"));

                // Chemin absolu vers la base SQLite (sinon le cwd du process packagé
                // pointe vers _internal/, pas vers le dossier de l'exe)
                let db_path = std::env::current_exe()
                    .ok()
                    .and_then(|p| p.parent().map(|p| p.join("data").join("chubot.db")))
                    .unwrap_or_else(|| std::path::PathBuf::from("./data/chubot.db"));
                let db_url = format!(
                    "sqlite+aiosqlite:///{}",
                    db_path.to_str().unwrap_or("./data/chubot.db").replace('\\', "/")
                );

                let (_rx, child) = app.shell()
                    .sidecar("chubot-backend")
                    .expect("sidecar introuvable")
                    .env("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,tauri://localhost,http://tauri.localhost")
                    .env("VECTOR_STORE_PATH", vector_store_path.to_str().unwrap_or("./data/indexes"))
                    .env("DATABASE_URL", db_url)
                    .spawn()
                    .expect("impossible de démarrer le backend");

                *app.state::<BackendProcess>().0.lock().unwrap() = Some(child);
            }

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
