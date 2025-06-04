from flask import Flask, Markup, request, jsonify
import ast # For safely evaluating literal Python structures

app = Flask(__name__)

# --- HTML, CSS, and JavaScript as a single string template ---
# The HTML/CSS for the UI layout remains largely the same.
# The main change is that one editor is now for Python code.

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Python-Powered Animation Playground</title>
    <style>
        /* CSS styles are the same as the previous version for UI layout */
        /* ... (pasting the full CSS here would make the response too long) ... */
        /* For brevity, I'll assume the CSS from the previous Flask example is here */
        :root {{
            --system-font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
            --bg-color: #f4f4f5; --pane-bg-color: #ffffff; --header-bg-color: #f9f9f9; --text-color: #1d1d1f; 
            --text-color-secondary: #6e6e73; --border-color: #dcdcdc; --textarea-bg-color: #ffffff;
            --textarea-text-color: #1d1d1f; --control-bg-color: rgba(248, 248, 248, 0.85); 
            --control-bg-color-rgb: 248, 248, 248; --button-bg-color: #e9e9eb; --button-text-color: #1d1d1f;
            --button-hover-bg-color: #dedee0; --button-active-bg-color: #d1d1d3; --button-border-color: transparent;
            --input-bg-color: #f0f0f0; --input-border-color: #c6c6c8; --shadow-color: rgba(0,0,0,0.06);
            --shadow-stronger-color: rgba(0,0,0,0.1); --accent-color: #007aff; --footer-text-color: #8a8a8e;
        }}
        body.dark-theme {{
            --bg-color: #1c1c1e; --pane-bg-color: #2c2c2e; --header-bg-color: #3a3a3c; --text-color: #f5f5f7;
            --text-color-secondary: #8e8e93; --border-color: #38383a; --textarea-bg-color: #2c2c2e;
            --textarea-text-color: #f5f5f7; --control-bg-color: rgba(30, 30, 32, 0.85);
            --control-bg-color-rgb: 30, 30, 32; --button-bg-color: #3a3a3c; --button-text-color: #f5f5f7;
            --button-hover-bg-color: #48484a; --button-active-bg-color: #545456; --button-border-color: transparent;
            --input-bg-color: #3a3a3c; --input-border-color: #545456; --shadow-color: rgba(0,0,0,0.2);
            --shadow-stronger-color: rgba(0,0,0,0.3); --footer-text-color: #636366;
        }}
        body {{ font-family: var(--system-font); margin: 0; display: flex; flex-direction: column; height: 100vh; background-color: var(--bg-color); color: var(--text-color); transition: background-color 0.3s, color 0.3s; font-size: 14px; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }}
        .editor-container {{ display: flex; flex-basis: 45%; min-height: 220px; gap: 15px; padding: 15px 15px 7px 15px; }}
        .editor-pane {{ display: flex; flex-direction: column; flex: 1; background-color: var(--pane-bg-color); border-radius: 12px; box-shadow: 0 3px 8px var(--shadow-color), 0 1px 2px var(--shadow-stronger-color); overflow: hidden; transition: background-color 0.3s, box-shadow 0.3s; }}
        .editor-pane h2 {{ margin: 0; padding: 12px 18px; background-color: var(--header-bg-color); font-size: 0.95em; font-weight: 500; color: var(--text-color); border-bottom: 1px solid var(--border-color); transition: background-color 0.3s, border-color 0.3s, color 0.3s; }}
        textarea {{ flex-grow: 1; padding: 12px 15px; border: none; outline: none; font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace; font-size: 0.9em; line-height: 1.5; resize: none; background-color: var(--textarea-bg-color); color: var(--textarea-text-color); transition: background-color 0.3s, color 0.3s; border-bottom-left-radius: 12px; border-bottom-right-radius: 12px; }}
        textarea:focus-visible {{ box-shadow: inset 0 0 0 2px var(--accent-color); }}
        .preview-container {{ flex-grow: 1; padding: 7px 15px 15px 15px; display: flex; flex-direction: column; }}
        .preview-header {{ display: flex; justify-content: space-between; align-items: center; margin: 0 0 8px 0; padding: 0 10px 0 18px; height: 48px; background-color: var(--pane-bg-color); font-weight: 500; color: var(--text-color); border-top-left-radius: 12px; border-top-right-radius: 12px; border: 1px solid var(--border-color); border-bottom: none; box-shadow: 0 3px 8px var(--shadow-color); transition: background-color 0.3s, border-color 0.3s, color 0.3s, box-shadow 0.3s; }}
        .preview-header h2 {{ margin: 0; padding: 0; font-size: 0.95em; font-weight: inherit; background-color: transparent; border: none; box-shadow: none; }}
        body.dark-theme .preview-header {{ background-color: var(--header-bg-color); }}
        #toggle-fullscreen-preview {{ display: flex; align-items: center; gap: 6px; padding: 6px 10px; background-color: var(--button-bg-color); border: 1px solid transparent; border-radius: 7px; color: var(--button-text-color); font-size: 0.85em; font-weight: 500; cursor: pointer; transition: background-color 0.2s, color 0.2s; }}
        #toggle-fullscreen-preview:hover {{ background-color: var(--button-hover-bg-color); }}
        .fullscreen-icon {{ font-size: 1.1em; line-height: 1; }}
        #preview-frame {{ flex-grow: 1; width: 100%; border: 1px solid var(--border-color); background-color: #fff; box-shadow: 0 3px 8px var(--shadow-color), 0 1px 2px var(--shadow-stronger-color); transition: border-color 0.3s, box-shadow 0.3s; }}
        body.dark-theme #preview-frame {{ background-color: var(--pane-bg-color); }}
        .preview-header + #preview-frame {{ border-top-left-radius: 0; border-top-right-radius: 0; border-top-color: transparent; }}
        .controls-container {{ padding: 12px 18px; background-color: var(--control-bg-color); backdrop-filter: blur(10px) saturate(180%); -webkit-backdrop-filter: blur(10px) saturate(180%); display: flex; flex-wrap: wrap; gap: 12px; align-items: center; box-shadow: 0 -2px 5px var(--shadow-color); border-top: 1px solid var(--border-color); transition: background-color 0.3s, border-color 0.3s; position: relative; z-index: 10; }}
        .controls-container button, .controls-container select, .controls-container input[type="text"] {{ padding: 8px 14px; border: 1px solid var(--button-border-color); border-radius: 8px; background-color: var(--button-bg-color); color: var(--button-text-color); cursor: pointer; font-size: 0.9em; font-weight: 500; transition: background-color 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }}
        .controls-container button:hover {{ background-color: var(--button-hover-bg-color); }}
        .controls-container button:active {{ background-color: var(--button-active-bg-color); box-shadow: inset 0 1px 2px rgba(0,0,0,0.1); }}
        .controls-container input[type="text"], .controls-container select {{ background-color: var(--input-bg-color); border: 1px solid var(--input-border-color); color: var(--text-color); box-shadow: inset 0 1px 2px rgba(0,0,0,0.03); }}
        .controls-container input[type="text"]:focus, .controls-container select:focus {{ outline: none; border-color: var(--accent-color); box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.3); }}
        .controls-container input[type="text"] {{ min-width: 160px; }}
        .controls-container label {{ font-size: 0.9em; color: var(--text-color-secondary); margin-right: 5px; }}
        .control-group {{ display: flex; align-items: center; gap: 8px; }}
        .spacer {{ flex-grow: 1; }}
        #delete-preset {{ padding: 8px 10px; }}
        #toggle-theme {{ padding: 8px 10px; }}
        .app-footer {{ padding: 10px 18px; text-align: center; font-size: 0.8em; color: var(--footer-text-color); background-color: var(--bg-color); border-top: 1px solid var(--border-color); transition: background-color 0.3s, color 0.3s, border-color 0.3s; }}
        body.preview-fullscreen .editor-container, body.preview-fullscreen .controls-container, body.preview-fullscreen .app-footer {{ display: none !important; }}
        body.preview-fullscreen .preview-container {{ position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; padding: 0; margin: 0; z-index: 1000; background-color: var(--bg-color); border-radius: 0; box-shadow: none; }}
        body.preview-fullscreen .preview-header {{ position: fixed; top: 15px; right: 15px; width: auto; height: auto; background-color: rgba(var(--control-bg-color-rgb), 0.7); backdrop-filter: blur(8px) saturate(150%); -webkit-backdrop-filter: blur(8px) saturate(150%); border: 1px solid rgba(var(--border-color),0.5); border-radius: 8px; box-shadow: 0 3px 10px var(--shadow-stronger-color); padding: 0; z-index: 1001; }}
        body.preview-fullscreen .preview-header h2 {{ display: none; }}
        body.preview-fullscreen #toggle-fullscreen-preview {{ background-color: transparent; border: none; padding: 10px 15px; font-size: 0.9em; }}
        body.preview-fullscreen #toggle-fullscreen-preview:hover {{ background-color: rgba(var(--button-hover-bg-color),0.5); }}
        body.preview-fullscreen #preview-frame {{ width: 100%; height: 100%; border: none; border-radius: 0; box-shadow: none; margin-top: 0; }}
        #python-editor-pane {{ flex: 2; }} /* Give Python editor more space */
        #placeholder-pane {{ flex: 1; background-color: transparent; box-shadow: none; }}
        #placeholder-pane h2 {{ visibility: hidden; }}
        #placeholder-pane textarea {{ display: none; }}
        .processing-indicator {{
            position: fixed; top: 10px; left: 50%; transform: translateX(-50%);
            background-color: var(--accent-color); color: white; padding: 5px 15px;
            border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 2000; display: none; /* Hidden by default */
        }}
    </style>
</head>
<body>
    <div class="processing-indicator" id="processing-indicator">Processing...</div>

    <div class="editor-container">
        <div class="editor-pane" id="python-editor-pane">
            <h2>Python Animation Definition</h2>
            <textarea id="python-editor" spellcheck="false" aria-label="Python Animation Definition Editor"></textarea>
        </div>
        <div class="editor-pane" id="placeholder-pane"> <!-- Placeholder for layout balance -->
             <h2></h2>
             <textarea></textarea>
        </div>
    </div>

    <div class="preview-container">
        <div class="preview-header">
            <h2>Live Preview</h2>
            <button id="toggle-fullscreen-preview" title="Toggle Fullscreen Preview">
                <span class="fullscreen-icon">🖼️</span>
                <span class="fullscreen-text">Fullscreen</span>
            </button>
        </div>
        <iframe id="preview-frame" sandbox="allow-scripts allow-same-origin" title="Live Preview of HTML and CSS"></iframe>
    </div>

    <div class="controls-container">
        <button id="run-python-button" title="Run Python Definition to Update Preview">▶️ Run Definition</button>
        <div class="control-group">
            <input type="text" id="preset-name" placeholder="Preset Name" aria-label="Preset Name">
            <button id="save-preset">Save Preset</button>
        </div>
        
        <div class="control-group">
            <label for="load-preset-select">Load Preset:</label>
            <select id="load-preset-select" aria-label="Load Preset">
                <option value="">-- Select Preset --</option>
            </select>
            <button id="delete-preset" title="Delete Selected Preset">🗑️ Delete</button>
        </div>

        <div class="control-group">
            <button id="copy-generated-html">Copy Gen. HTML</button>
            <button id="copy-generated-css">Copy Gen. CSS</button>
        </div>
        <div class="control-group">
            <button id="download-generated-html">Download Gen. HTML</button>
            <!-- <button id="download-css">Download CSS</button> Removed as CSS is now fully generated -->
        </div>
        <div class="spacer"></div>
        <button id="toggle-theme" title="Toggle Light/Dark Theme">🌓 Theme</button>
    </div>

    <footer class="app-footer">
        <p>&copy; <span id="current-year"></span> Kirati Rattanaporn (win). All Rights Reserved.</p>
    </footer>

    <script>
        const pythonEditor = document.getElementById('python-editor');
        const previewFrame = document.getElementById('preview-frame');
        const runPythonButton = document.getElementById('run-python-button');
        const processingIndicator = document.getElementById('processing-indicator');
        
        const savePresetButton = document.getElementById('save-preset');
        const loadPresetSelect = document.getElementById('load-preset-select');
        const deletePresetButton = document.getElementById('delete-preset');
        const presetNameInput = document.getElementById('preset-name');

        const copyGeneratedHtmlButton = document.getElementById('copy-generated-html');
        const copyGeneratedCssButton = document.getElementById('copy-generated-css');
        const downloadGeneratedHtmlButton = document.getElementById('download-generated-html');
        
        const toggleThemeButton = document.getElementById('toggle-theme');
        const toggleFullscreenButton = document.getElementById('toggle-fullscreen-preview');
        const currentYearSpan = document.getElementById('current-year');

        const PRESETS_STORAGE_KEY = 'pythonAnimationPlaygroundPresets_v1';
        const THEME_STORAGE_KEY = 'pythonAnimationPlaygroundTheme_v1';
        const LAST_CONTENT_STORAGE_KEY = 'pythonAnimationPlaygroundLastContent_v1';

        let lastGeneratedHTML = '';
        let lastGeneratedCSS = '';

        async function runPythonDefinition() {
            const pythonCode = pythonEditor.value;
            if (!pythonCode.trim()) {
                updatePreview('', ''); // Clear preview if no code
                return;
            }
            localStorage.setItem(LAST_CONTENT_STORAGE_KEY, pythonCode);
            processingIndicator.style.display = 'block';

            try {
                const response = await fetch('/generate_animation', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ python_code: pythonCode })
                });
                
                processingIndicator.style.display = 'none';

                if (response.ok) {
                    const data = await response.json();
                    if (data.error) {
                        alert("Error generating animation: " + data.error);
                        updatePreview('', ''); // Clear preview on error
                    } else {
                        lastGeneratedHTML = data.html || '';
                        lastGeneratedCSS = data.css || '';
                        updatePreview(lastGeneratedHTML, lastGeneratedCSS);
                    }
                } else {
                    const errorData = await response.json();
                    alert("Server error: " + (errorData.error || response.statusText));
                    updatePreview('', '');
                }
            } catch (error) {
                processingIndicator.style.display = 'none';
                alert("Network or client-side error: " + error.message);
                updatePreview('', '');
            }
        }

        function updatePreview(htmlContent, cssContent) {
            const previewDocument = previewFrame.contentDocument || previewFrame.contentWindow.document;
            previewDocument.open();
            previewDocument.write(\`
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body { margin: 0; padding: 10px; box-sizing: border-box; font-family: \${getComputedStyle(document.body).fontFamily}; }
                        \${cssContent}
                    </style>
                </head>
                <body>
                    \${htmlContent}
                </body>
                </html>
            \`);
            previewDocument.close();
        }
        
        runPythonButton.addEventListener('click', runPythonDefinition);
        // Optionally run on Ctrl+Enter or similar from textarea
        pythonEditor.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                runPythonDefinition();
            }
        });


        // --- Preset Management (saves/loads Python code) ---
        function getPresets() {
            const presetsJson = localStorage.getItem(PRESETS_STORAGE_KEY);
            return presetsJson ? JSON.parse(presetsJson) : [];
        }

        function savePresets(presets) {
            localStorage.setItem(PRESETS_STORAGE_KEY, JSON.stringify(presets));
            populatePresetDropdown();
        }

        function populatePresetDropdown() {
            const presets = getPresets();
            const currentSelectedValue = loadPresetSelect.value;
            loadPresetSelect.innerHTML = '<option value="">-- Select Preset --</option>';
            presets.sort((a, b) => a.name.localeCompare(b.name));
            presets.forEach(preset => {
                const option = document.createElement('option');
                option.value = preset.id;
                option.textContent = preset.name;
                loadPresetSelect.appendChild(option);
            });
            if (presets.find(p => p.id === currentSelectedValue)) {
                loadPresetSelect.value = currentSelectedValue;
            }
        }

        savePresetButton.addEventListener('click', () => {
            const name = presetNameInput.value.trim();
            if (!name) {
                alert('Please enter a name for the preset.');
                presetNameInput.focus();
                return;
            }
            const pythonCode = pythonEditor.value;
            if (!pythonCode.trim()) {
                alert('Python definition is empty. Nothing to save.');
                return;
            }

            let presets = getPresets();
            const existingPreset = presets.find(p => p.name === name);
            if (existingPreset) {
                if (confirm(\`Preset "\${name}" already exists. Overwrite?\`)) {
                    existingPreset.code = pythonCode;
                } else { return; }
            } else {
                presets.push({ id: Date.now().toString(), name, code: pythonCode });
            }
            savePresets(presets);
            alert(\`Preset "\${name}" saved!\`);
            const savedPreset = presets.find(p => p.name === name);
            if (savedPreset) loadPresetSelect.value = savedPreset.id;
        });

        loadPresetSelect.addEventListener('change', async () => {
            const selectedValue = loadPresetSelect.value;
            if (selectedValue === "") {
                presetNameInput.value = '';
                pythonEditor.value = '';
                updatePreview('',''); // Clear preview
                return;
            }
            const presets = getPresets();
            const selectedPreset = presets.find(p => p.id === selectedValue);
            if (selectedPreset) {
                pythonEditor.value = selectedPreset.code;
                presetNameInput.value = selectedPreset.name;
                await runPythonDefinition(); // Run loaded definition
            }
        });

        deletePresetButton.addEventListener('click', () => {
            const selectedValue = loadPresetSelect.value;
            if (selectedValue === "") { alert('Select preset to delete.'); return; }
            let presets = getPresets();
            const selectedPreset = presets.find(p => p.id === selectedValue);
            if (selectedPreset && confirm(\`Delete preset "\${selectedPreset.name}"?\`)) {
                presets = presets.filter(p => p.id !== selectedValue);
                savePresets(presets);
                presetNameInput.value = '';
                pythonEditor.value = ''; 
                updatePreview('','');
                alert(\`Preset "\${selectedPreset.name}" deleted.\`);
                if (loadPresetSelect.options.length > 1) loadPresetSelect.selectedIndex = 0;
            }
        });

        // --- Export Generated Code Functionality ---
        function copyToClipboard(text, type) {
            navigator.clipboard.writeText(text).then(() => {
                alert(\`Generated \${type} copied to clipboard!\`);
            }).catch(err => alert(\`Failed to copy generated \${type}.\`));
        }

        copyGeneratedHtmlButton.addEventListener('click', () => {
            if (!lastGeneratedHTML) { alert("No HTML generated yet. Run a definition first."); return; }
            copyToClipboard(lastGeneratedHTML, 'HTML');
        });
        copyGeneratedCssButton.addEventListener('click', () => {
            if (!lastGeneratedCSS) { alert("No CSS generated yet. Run a definition first."); return; }
            copyToClipboard(lastGeneratedCSS, 'CSS');
        });
        
        function downloadFile(filename, content, mimeType) {
            const element = document.createElement('a');
            const blob = new Blob([content], {type: mimeType});
            element.href = URL.createObjectURL(blob);
            element.setAttribute('download', filename);
            document.body.appendChild(element);
            element.click();
            document.body.removeChild(element);
            URL.revokeObjectURL(element.href);
        }

        downloadGeneratedHtmlButton.addEventListener('click', () => {
            if (!lastGeneratedHTML && !lastGeneratedCSS) {
                alert("Nothing generated yet. Run a definition first."); return;
            }
            const completeHtml = \`<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Python-Generated Animation</title>
<style>
body { font-family: \${getComputedStyle(document.body).fontFamily}; }
\${lastGeneratedCSS}
</style>
</head>
<body>
\${lastGeneratedHTML}
</body></html>\`;
            downloadFile('python_animation.html', completeHtml, 'text/html');
        });


        // --- Theme Toggle (same as before) ---
        function applyTheme(theme) {
            document.body.classList.toggle('dark-theme', theme === 'dark');
            toggleThemeButton.textContent = theme === 'dark' ? '☀️' : '🌙';
            toggleThemeButton.title = \`Switch to \${theme === 'dark' ? 'Light' : 'Dark'} Theme\`;
            localStorage.setItem(THEME_STORAGE_KEY, theme);
        }
        toggleThemeButton.addEventListener('click', () => {
            const currentTheme = document.body.classList.contains('dark-theme') ? 'dark' : 'light';
            applyTheme(currentTheme === 'light' ? 'dark' : 'light');
        });

        // --- Fullscreen Preview Toggle (same as before) ---
        function setPreviewFullscreen(isFullscreen) {
            document.body.classList.toggle('preview-fullscreen', isFullscreen);
            const icon = toggleFullscreenButton.querySelector('.fullscreen-icon');
            const text = toggleFullscreenButton.querySelector('.fullscreen-text');
            if (icon) icon.textContent = isFullscreen ? '✖️' : '🖼️';
            if (text) text.textContent = isFullscreen ? 'Exit' : 'Fullscreen';
            toggleFullscreenButton.title = \`\${isFullscreen ? 'Exit' : 'Toggle'} Fullscreen Preview\`;
        }
        toggleFullscreenButton.addEventListener('click', () => setPreviewFullscreen(!document.body.classList.contains('preview-fullscreen')));
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && document.body.classList.contains('preview-fullscreen')) setPreviewFullscreen(false);
        });

        // --- Initial Load ---
        function initializeApp() {
            if(currentYearSpan) currentYearSpan.textContent = new Date().getFullYear();
            
            const savedTheme = localStorage.getItem(THEME_STORAGE_KEY) || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
            applyTheme(savedTheme);

            populatePresetDropdown();
            
            const lastPythonCode = localStorage.getItem(LAST_CONTENT_STORAGE_KEY);
            let initialCodeToRun = '';

            if (lastPythonCode) {
                pythonEditor.value = lastPythonCode;
                initialCodeToRun = lastPythonCode;
            } else {
                const presets = getPresets();
                if (presets.length === 0) { // Add default examples if no user presets
                    const defaultExamples = [
                        { id: "py_ex1", name: "Python: Simple Bounce Box", code: 
`animation_config = {
    "html_content": "<div class='my-element'>Hello Python!</div>",
    "css_rules": {
        ".my-element": {
            "width": "150px", "height": "70px", "background-color": "var(--accent-color)",
            "color": "white", "display": "flex", "align-items": "center",
            "justify-content": "center", "border-radius": "8px", "margin": "50px auto",
            "font-weight": "bold"
        }
    },
    "animation": {
        "name": "bounceEffect",
        "target_selector": ".my-element",
        "duration": "2s",
        "iteration_count": "infinite",
        "timing_function": "ease-in-out",
        "keyframes": [
            {"percent": 0, "styles": {"transform": "translateY(0px)"}},
            {"percent": 50, "styles": {"transform": "translateY(-30px) scale(1.1)"}},
            {"percent": 100, "styles": {"transform": "translateY(0px)"}}
        ]
    }
}`
                        },
                        { id: "py_ex2", name: "Python: Pulse", code:
`animation_config = {
    "html_content": "<div class='pulsar'></div>",
    "css_rules": {
        ".pulsar": {
            "width": "80px", "height": "80px", "background-color": "#ff5722",
            "border-radius": "50%", "margin": "50px auto",
            "box-shadow": "0 0 0 0 rgba(255, 87, 34, 0.7)"
        }
    },
    "animation": {
        "name": "pulseAnim", "target_selector": ".pulsar", "duration": "1.5s",
        "iteration_count": "infinite", "timing_function": "ease-out",
        "keyframes": [
            {"percent": 0, "styles": {"transform": "scale(0.9)", "box-shadow": "0 0 0 0 rgba(255, 87, 34, 0.7)"}},
            {"percent": 70, "styles": {"transform": "scale(1)", "box-shadow": "0 0 0 20px rgba(255, 87, 34, 0)"}},
            {"percent": 100, "styles": {"transform": "scale(0.9)", "box-shadow": "0 0 0 0 rgba(255, 87, 34, 0)"}}
        ]
    }
}`
                        }
                    ];
                    savePresets(defaultExamples); // This also populates dropdown
                    pythonEditor.value = defaultExamples[0].code;
                    presetNameInput.value = defaultExamples[0].name;
                    loadPresetSelect.value = defaultExamples[0].id;
                    initialCodeToRun = defaultExamples[0].code;
                } else if (presets.length > 0) {
                    pythonEditor.value = presets[0].code;
                    presetNameInput.value = presets[0].name;
                    loadPresetSelect.value = presets[0].id;
                    initialCodeToRun = presets[0].code;
                }
            }
            if (initialCodeToRun) runPythonDefinition(); // Run initial definition
            else updatePreview('', ''); // Clear if nothing to run
        }
        document.addEventListener('DOMContentLoaded', initializeApp);
    </script>
</body>
</html>
"""

# --- Python Backend Logic for Animation Generation ---

def generate_css_from_rules(rules_dict):
    """Generates CSS string from a dictionary of rules."""
    css_string = ""
    for selector, styles in rules_dict.items():
        css_string += f"{selector} {{\n"
        for prop, value in styles.items():
            css_string += f"  {prop}: {value};\n"
        css_string += "}\n"
    return css_string

def generate_keyframes_css(kf_name, keyframes_list):
    """Generates @keyframes CSS string."""
    kf_string = f"@keyframes {kf_name} {{\n"
    for keyframe in keyframes_list:
        percent = keyframe.get("percent", keyframe.get("offset", 0)) # Allow 'offset' or 'percent'
        kf_string += f"  {percent}% {{\n"
        for prop, value in keyframe.get("styles", {}).items():
            kf_string += f"    {prop}: {value};\n"
        kf_string += "  }\n"
    kf_string += "}\n"
    return kf_string

@app.route('/')
def home():
    return Markup(HTML_TEMPLATE)

@app.route('/generate_animation', methods=['POST'])
def generate_animation_endpoint():
    try:
        data = request.get_json()
        python_code_str = data.get('python_code', '')

        if not python_code_str.strip():
            return jsonify({"html": "", "css": "", "error": "No Python code provided."})

        # IMPORTANT: Safely evaluate the Python string.
        # ast.literal_eval can only parse literals (strings, numbers, tuples, lists, dicts, booleans, None).
        # It CANNOT execute functions or arbitrary code, making it much safer than exec() or eval().
        # For this to work, the user's Python code must result in a single literal expression
        # (e.g., assigning to a variable like `animation_config = {...}` at the end).
        # We'll look for a variable named 'animation_config'.

        # To extract 'animation_config', we can parse the module and look for an assignment.
        parsed_code = ast.parse(python_code_str)
        config_dict = None
        for node in parsed_code.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'animation_config':
                        # Safely evaluate the assigned value
                        config_dict = ast.literal_eval(node.value)
                        break
                if config_dict is not None:
                    break
        
        if config_dict is None or not isinstance(config_dict, dict):
            return jsonify({"html": "", "css": "", "error": "Python code must define a dictionary variable named 'animation_config'."})


        html_content = config_dict.get("html_content", "")
        css_rules = config_dict.get("css_rules", {})
        animation_details = config_dict.get("animation", {})

        generated_css = ""
        if css_rules:
            generated_css += generate_css_from_rules(css_rules)
        
        if animation_details:
            kf_name = animation_details.get("name", "myCustomAnimation")
            kf_list = animation_details.get("keyframes", [])
            target_selector = animation_details.get("target_selector")
            
            if kf_list:
                generated_css += generate_keyframes_css(kf_name, kf_list)
            
            if target_selector:
                anim_props_css = f"{target_selector} {{\n"
                anim_props_css += f"  animation-name: {kf_name};\n"
                if "duration" in animation_details:
                    anim_props_css += f"  animation-duration: {animation_details['duration']};\n"
                if "timing_function" in animation_details:
                    anim_props_css += f"  animation-timing-function: {animation_details['timing_function']};\n"
                if "delay" in animation_details:
                    anim_props_css += f"  animation-delay: {animation_details['delay']};\n"
                if "iteration_count" in animation_details:
                    anim_props_css += f"  animation-iteration-count: {animation_details['iteration_count']};\n"
                if "direction" in animation_details:
                    anim_props_css += f"  animation-direction: {animation_details['direction']};\n"
                if "fill_mode" in animation_details:
                    anim_props_css += f"  animation-fill-mode: {animation_details['fill_mode']};\n"
                anim_props_css += "}\n"
                generated_css += anim_props_css
        
        return jsonify({"html": html_content, "css": generated_css})

    except ast.ASTError as e: # Catch errors from ast.parse
        return jsonify({"html": "", "css": "", "error": f"Python code parsing error: {e}"}), 400
    except ValueError as e: # Catch errors from ast.literal_eval if structure is not a literal
        return jsonify({"html": "", "css": "", "error": f"Invalid Python literal structure: {e}"}), 400
    except Exception as e:
        # Log the full error for debugging on the server
        app.logger.error(f"Error processing animation definition: {e}", exc_info=True)
        return jsonify({"html": "", "css": "", "error": f"An unexpected error occurred: {str(e)}"}), 500


if __name__ == '__main__':
    print("Python-Powered CSS Animation Playground")
    print("Ensure you have Flask installed: pip install Flask")
    print("Run the script and navigate to http://127.0.0.1:5000/ in your web browser.")
    app.run(debug=True)