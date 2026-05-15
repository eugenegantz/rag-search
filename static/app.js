const API_BASE = '';

const ALLOWED_EXTENSIONS = ['.docx', '.pdf', '.txt', '.md', '.html', '.jpeg', '.jpg', '.png'];

function validateFilePath(path) {
    if (/^http(s?):\/\//ig.test(path)) {
        return true
    }
    const ext = path.toLowerCase().slice(path.lastIndexOf('.'));
    return ALLOWED_EXTENSIONS.includes(ext);
}

function getFileExtension(path) {
    return path.toLowerCase().slice(path.lastIndexOf('.'));
}

function showStatus(elementId, message, type = 'info') {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.textContent = message;
    el.className = 'b-status b-status_' + type;
    el.style.display = 'block';
}

function hideStatus(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.style.display = 'none';
}

function setLoading(buttonId, isLoading) {
    const btn = document.getElementById(buttonId);
    if (!btn) return;
    btn.disabled = isLoading;
    if (isLoading) {
        btn.innerHTML = '<span class="b-spinner"></span> Обработка...';
    } else {
        btn.textContent = btn.dataset.originalText || 'Отправить';
    }
}

async function searchDocuments() {
    const queryInput = document.getElementById('query');
    // const topKInput = document.getElementById('top_k');
    const resultsDiv = document.getElementById('results');

    const query = queryInput.value.trim();
    // const topK = parseInt(topKInput.value) || 5;

    if (!query) {
        showStatus('search-status', 'Введите поисковый запрос', 'error');
        return;
    }

    hideStatus('search-status');
    setLoading('search-btn', true);

    try {
        const response = await fetch(`${API_BASE}/api/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query,
                // top_k: topK
            })
        });

        const data = await response.json();

        if (data.error) {
            showStatus('search-status', data.error, 'error');
            resultsDiv.innerHTML = '';
        } else {
            showStatus('search-status', `Найдено результатов: ${data.results?.length || 0}`, 'success');
            renderResults(data.results || []);
        }
    } catch (err) {
        showStatus('search-status', 'Ошибка соединения с сервером', 'error');
        resultsDiv.innerHTML = '';
    } finally {
        setLoading('search-btn', false);
    }
}

function isImagePath(path) {
    const ext = getFileExtension(path);
    return ['.jpeg', '.jpg', '.png'].includes(ext);
}

function renderResults(results) {
    const resultsDiv = document.getElementById('results');

    if (!results || results.length === 0) {
        resultsDiv.innerHTML = '<div class="b-empty">Ничего не найдено</div>';
        return;
    }

    let html = '';

    // results[0] — файловый поиск (изображения)
    if (results[0] && results[0].refs && results[0].refs.length > 0) {
        const imageRefs = results[0].refs.filter(ref => isImagePath(ref.filepath));
        const otherRefs = results[0].refs.filter(ref => !isImagePath(ref.filepath));

        if (imageRefs.length > 0 || otherRefs.length > 0) {
            html += '<div class="b-result"><div class="b-result__refs-title">Найденные файлы:</div>';

            if (imageRefs.length > 0) {
                html += '<div class="b-image-grid">';
                html += imageRefs.map(ref => {
                    const href = "/files/" + encodeURIComponent(ref.filepath);
                    return (
                        `<div class="b-image-item">
                            <a href="${href}" class="b-image-item__link" target="_blank">
                                <img class="b-image-item__thumb" src="${href}" alt="" loading="lazy">
                                <div class="b-image-item__path">${ref.filepath}</div>
                            </a>
                        </div>`
                    );
                }).join('');
                html += '</div>';
            }

            if (otherRefs.length > 0) {
                html += '<ol class="b-result__refs-list">';
                html += otherRefs.map(ref => {
                    const href = "/files/" + encodeURIComponent(ref.filepath);
                    return (
                        `<li class="b-result__ref">
                            <div class="b-result__ref-path">[${(ref.id || '')}]. <a href="${href}">${ref.filepath}</a></div>
                            <div class="b-result__ref-note">${(ref.note || '')}</div>
                        </li>`
                    )
                }).join('');
                html += '</ol>';
            }

            html += '</div>';
        }
    }

    // results[1] — LLM поиск
    if (results[1] && (results[1].content || (results[1].refs && results[1].refs.length > 0))) {
        const rawHtml = marked.parse(results[1].content || '');
        const cleanHtml = DOMPurify.sanitize(rawHtml);

        html += `<div class="b-result">
            <div class="b-result__content b-markdown">${cleanHtml}</div>`;

        if (results[1].refs && results[1].refs.length > 0) {
            html += `<div class="b-result__refs">
                <div class="b-result__refs-title">Источники:</div>
                <ol class="b-result__refs-list">
                    ${results[1].refs.map(ref => {
                        const href = "/files/" + encodeURIComponent(ref.filepath);
                        return (
                            `<li class="b-result__ref">
                                <div class="b-result__ref-path">
                                    [${(ref.id || '')}].
                                    <a href="${href}" target="_blank">${ref.filepath}</a>
                                </div>
                                <div class="b-result__ref-note">${(ref.note || '')}</div>
                            </li>`
                        )
                    }).join('')}
                </ol>
            </div>`;
        }

        html += '</div>';
    }

    if (!html) {
        resultsDiv.innerHTML = '<div class="b-empty">Ничего не найдено</div>';
        return;
    }

    resultsDiv.innerHTML = html;
}

async function searchFiles() {
    const queryInput = document.getElementById('query');
    const resultsDiv = document.getElementById('search-files-results');

    if (!resultsDiv) return;

    const query = queryInput.value.trim();

    if (!query) {
        showStatus('search-files-status', 'Введите поисковый запрос', 'error');
        return;
    }

    hideStatus('search-files-status');
    setLoading('search-files-btn', true);

    try {
        const response = await fetch(`${API_BASE}/api/index/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        const data = await response.json();

        if (data.error) {
            showStatus('search-files-status', data.error, 'error');
            resultsDiv.innerHTML = '';
        } else {
            const metas = data.meta || [];
            showStatus('search-files-status', `Найдено файлов: ${metas.length}`, 'success');
            renderFileResults(metas);
        }
    } catch (err) {
        showStatus('search-files-status', 'Ошибка соединения с сервером', 'error');
        resultsDiv.innerHTML = '';
    } finally {
        setLoading('search-files-btn', false);
    }
}

function renderFileResults(metas) {
    const resultsDiv = document.getElementById('search-files-results');

    if (!metas || metas.length === 0) {
        resultsDiv.innerHTML = '<div class="b-empty">Ничего не найдено</div>';
        return;
    }

    const imageMetas = metas.filter(m => isImagePath(m.filepath));
    const otherMetas = metas.filter(m => !isImagePath(m.filepath));

    let html = '<div class="b-result">';

    if (imageMetas.length > 0) {
        html += '<div class="b-result__refs-title">Изображения:</div>';
        html += '<div class="b-image-grid">';
        html += imageMetas.map(meta => {
            const href = "/files/" + encodeURIComponent(meta.filepath);
            return (
                `<div class="b-image-item">
                    <a href="${href}" class="b-image-item__link" target="_blank">
                        <img class="b-image-item__thumb" src="${href}" alt="" loading="lazy">
                        <div class="b-image-item__path">${meta.filepath}</div>
                    </a>
                </div>`
            );
        }).join('');
        html += '</div>';
    }

    if (otherMetas.length > 0) {
        html += '<div class="b-result__refs-title" style="margin-top: 1rem;">Файлы:</div>';
        html += '<ol class="b-result__refs-list">';
        html += otherMetas.map(meta => {
            const href = "/files/" + encodeURIComponent(meta.filepath);
            return (
                `<li class="b-result__ref">
                    <a href="${href}" target="_blank">
                        <div class="b-result__ref-path">${meta.filepath}</div>
                        <div class="b-result__ref-note">${(meta.note || '')}</div>
                    </a>
                </li>`
            );
        }).join('');
        html += '</ol>';
    }

    html += '</div>';
    resultsDiv.innerHTML = html;
}

async function addDocument() {
    const inputFilepath = document.getElementById('file_path');

    const filepathArray = inputFilepath.value.trim().split("\n").filter(s => s.trim())

    if (!filepathArray.length) {
        showStatus('add-status', 'Введите путь к файлу', 'error');
        return;
    }

    for (let filepath of filepathArray) {
        if (!validateFilePath(filepath)) {
            showStatus(
                'add-status', 
                `Неподдерживаемый формат. Разрешены: ${ALLOWED_EXTENSIONS.join(', ')}`, 
                'error'
            );
            return;
        }
    }

    hideStatus('add-status');
    setLoading('add-btn', true);

    try {
        const response = await fetch(`${API_BASE}/api/index/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filepath: filepathArray })
        });

        const data = await response.json();

        if (data.error) {
            showStatus('add-status', data.error, 'error');
        } else {
            showStatus('add-status', data.message || 'Документ успешно добавлен в индекс', 'success');
            inputFilepath.value = '';
        }
    } catch (err) {
        showStatus('add-status', 'Ошибка соединения с сервером', 'error');
    } finally {
        setLoading('add-btn', false);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const searchBtn = document.getElementById('search-btn');
    if (searchBtn) {
        searchBtn.dataset.originalText = searchBtn.textContent;
        searchBtn.addEventListener('click', searchDocuments);
    }

    const searchFilesBtn = document.getElementById('search-files-btn');
    if (searchFilesBtn) {
        searchFilesBtn.dataset.originalText = searchFilesBtn.textContent;
        searchFilesBtn.addEventListener('click', searchFiles);
    }

    const addBtn = document.getElementById('add-btn');
    if (addBtn) {
        addBtn.dataset.originalText = addBtn.textContent;
        addBtn.addEventListener('click', addDocument);
    }

    const currentPath = window.location.pathname;
    document.querySelectorAll('.b-nav__link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('b-nav__link_active');
        }
    });

    const pathInput = document.getElementById('file_path');

    if (pathInput) {
        pathInput.placeholder = ""
            + "Построчно:"
            + "\nZ:/abc/Статья.docx"
            + "\nZ:/abc/Договор.pdf"
            + "\nZ:/abc/Заметки.txt"
            + "\nZ:/abc/Инструкция.md"
            + "\nZ:/abc/Страница.html"
            + "\nZ:/abc/Фото.jpg"
            + "\nZ:/abc/Скриншот.png"
            + "\nhttps://website.com/page"
    }
});
