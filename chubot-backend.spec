# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

datas_uvi,   bins_uvi,   hiddens_uvi   = collect_all('uvicorn')
datas_fast,  bins_fast,  hiddens_fast  = collect_all('fastapi')
datas_star,  bins_star,  hiddens_star  = collect_all('starlette')
datas_lc,    bins_lc,    hiddens_lc    = collect_all('langchain')
datas_lcc,   bins_lcc,   hiddens_lcc   = collect_all('langchain_core')
datas_lccom, bins_lccom, hiddens_lccom = collect_all('langchain_community')
datas_lcol,  bins_lcol,  hiddens_lcol  = collect_all('langchain_ollama')
datas_lcch,  bins_lcch,  hiddens_lcch  = collect_all('langchain_chroma')
datas_chr,   bins_chr,   hiddens_chr   = collect_all('chromadb')
datas_pyd,   bins_pyd,   hiddens_pyd   = collect_all('pydantic')
datas_pyds,  bins_pyds,  hiddens_pyds  = collect_all('pydantic_settings')

all_datas = (
    datas_uvi + datas_fast + datas_star +
    datas_lc + datas_lcc + datas_lccom + datas_lcol + datas_lcch +
    datas_chr + datas_pyd + datas_pyds +
    [('.env', '.'),
     ('bot/__init__.py', 'bot'),
     ('bot/api', 'bot/api'),
     ('bot/config', 'bot/config'),
     ('bot/ingestion', 'bot/ingestion'),
     ('bot/retrieval', 'bot/retrieval')]
)

all_bins = (
    bins_uvi + bins_fast + bins_star +
    bins_lc + bins_lcc + bins_lccom + bins_lcol + bins_lcch +
    bins_chr + bins_pyd + bins_pyds
)

all_hiddens = (
    hiddens_uvi + hiddens_fast + hiddens_star +
    hiddens_lc + hiddens_lcc + hiddens_lccom + hiddens_lcol + hiddens_lcch +
    hiddens_chr + hiddens_pyd + hiddens_pyds +
    collect_submodules('aiosqlite') +
    collect_submodules('sqlalchemy') +
    collect_submodules('flashrank') +
    collect_submodules('rank_bm25') +
    collect_submodules('uvicorn') +
    [
        # uvicorn explicit (PyInstaller ne les détecte pas toujours automatiquement)
        'uvicorn', 'uvicorn.main', 'uvicorn.config', 'uvicorn.server',
        'uvicorn.lifespan', 'uvicorn.lifespan.off', 'uvicorn.lifespan.on',
        'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl', 'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.protocols.websockets.wsproto_impl',
        'uvicorn.loops', 'uvicorn.loops.asyncio', 'uvicorn.loops.auto',
        'uvicorn.middleware', 'uvicorn.middleware.asgi2',
        'uvicorn.middleware.message_logger', 'uvicorn.middleware.proxy_headers',
        'uvicorn.workers',
        'h11', 'h11._connection', 'h11._events', 'h11._readers', 'h11._writers',
        'h11._util', 'h11._state', 'h11._headers',
        'aiosqlite', 'aiosqlite.core',
        'sqlalchemy.dialects.sqlite', 'sqlalchemy.dialects.sqlite.aiosqlite',
        'langchain_classic', 'langchain_classic.retrievers',
        'langchain_classic.retrievers.ensemble',
        'langchain_text_splitters',
        'bs4', 'lxml', 'openpyxl', 'docx2txt', 'pymupdf',
        'trafilatura', 'multipart', 'dotenv',
    ]
)

a = Analysis(
    ['backend_main.py'],
    pathex=['.'],
    binaries=all_bins,
    datas=all_datas,
    hiddenimports=all_hiddens,
    hookspath=[],
    runtime_hooks=[],
    # 'magic' (python-magic) segfault au chargement sur cette machine (libmagic cassée/absente) —
    # non utilisé par le code de l'app (Excel géré via openpyxl dans bot/ingestion/loaders.py),
    # seulement une dépendance transitive inutilisée de unstructured[xlsx].
    excludes=['playwright', 'pytest', 'notebook', 'matplotlib', 'torch', 'magic'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='chubot-backend',
    debug=False,
    strip=False,
    upx=False,
    console=True,
    target_arch=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='chubot-backend',
)
