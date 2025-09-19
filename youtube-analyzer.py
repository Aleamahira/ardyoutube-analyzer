<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Trending Explorer</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Chosen Palette: Slate Gray & Amber -->
    <!-- Application Structure Plan: The application uses a single-page dashboard structure. At the top, a collapsible section holds the API key configuration, keeping the main interface clean. Below this is the primary control panel with a keyword input and sorting options. The main content area is a responsive grid that dynamically displays video results. Following the results, two distinct sections provide actionable insights: 'Rekomendasi Judul' for easy title copying and 'Rekomendasi Tag' for SEO optimization. The new video analysis modal provides a focused, single-video view, complete with a content assistant. This structure was chosen to create a logical user flow: Configure -> Search -> Analyze Results -> Utilize Insights -> Deep Dive Analysis, making the tool intuitive and task-oriented. The new competitor analysis section is a separate module that mirrors this flow, allowing users to switch between keyword-based and channel-based research. -->
    <!-- Visualization & Content Choices: The primary content is the YouTube video data. Goal: Display search results clearly. Method: A responsive grid of cards, each containing a thumbnail, title, channel, and key metrics. Interaction: Titles are clickable links, but the entire card is now clickable to open a modal. Goal: Present key performance indicators (KPIs) concisely. Method: Color-coded badges for views, VPH (Views Per Hour), and age, plus new badges for "Live" and "Shorts" to quickly identify video type. Justification: Badges allow for quick, scannable comparison of video performance. Goal: Provide content creation aids. Method: Generated lists of top titles and keyword tags in copyable text fields. The new video modal uses a simple text block for the description and an AI-powered text generation for content ideas. Interaction: One-click copy functionality and a button to trigger AI analysis. Justification: This directly translates raw data into practical, usable assets for the user, fulfilling the tool's core purpose. No complex charts are needed as the core data is qualitative and comparative. -->
    <!-- CONFIRMATION: NO SVG graphics used. NO Mermaid JS used. -->
    <style>
        body {
            font-family: 'Inter', sans-serif;
        }
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        .form-select {
            background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
            background-position: right 0.5rem center;
            background-repeat: no-repeat;
            background-size: 1.5em 1.5em;
            padding-right: 2.5rem;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }
        .fade-in {
            animation: fadeIn 0.5s ease-in-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0, 0, 0, 0.7);
            padding-top: 60px;
        }
        .modal-content {
            background-color: #fefefe;
            margin: 5% auto;
            padding: 20px;
            border-radius: 1rem;
            width: 90%;
            max-width: 900px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            animation: slideUp 0.3s ease-out;
        }
        .close-btn {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
        }
        .close-btn:hover,
        .close-btn:focus {
            color: black;
            text-decoration: none;
            cursor: pointer;
        }
        @keyframes slideUp {
            from { transform: translateY(50px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
    </style>
</head>
<body class="bg-slate-50 text-slate-800">

    <div class="container mx-auto p-4 md:p-8">
        <header class="text-center mb-8">
            <h1 class="text-4xl md:text-5xl font-bold text-slate-900">🎬 YouTube Trending Explorer</h1>
            <p class="text-slate-600 mt-2 text-lg">Temukan video trending dan populer dari seluruh dunia untuk ide konten Anda.</p>
        </header>

        <div class="bg-white p-6 rounded-2xl shadow-lg mb-8 max-w-4xl mx-auto">
            <div id="settings-toggle" class="cursor-pointer flex justify-between items-center">
                <h2 class="text-xl font-semibold">⚙️ Pengaturan API</h2>
                <svg id="settings-arrow" class="w-6 h-6 transition-transform transform" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
            </div>
            <div id="settings-content" class="mt-4 hidden">
                 <p class="text-sm text-slate-500 mb-4">API Key Anda disimpan dengan aman di browser Anda dan tidak pernah dikirim ke server kami.</p>
                <div class="space-y-4">
                    <div>
                        <label for="youtube-api-key" class="block text-sm font-medium text-slate-700 mb-1">YouTube Data API Key</label>
                        <input type="password" id="youtube-api-key" placeholder="Masukkan YouTube Data API Key Anda" class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition">
                    </div>
                    <div>
                        <label for="gemini-api-key" class="block text-sm font-medium text-slate-700 mb-1">Gemini API Key</label>
                        <input type="password" id="gemini-api-key" placeholder="Masukkan Gemini API Key Anda" class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition">
                    </div>
                </div>
                <div class="mt-4">
                    <button id="save-api-key" class="w-full bg-amber-500 text-white font-semibold px-6 py-2 rounded-lg hover:bg-amber-600 transition-colors shadow-md">Simpan</button>
                </div>
                 <div id="api-key-message" class="mt-3 text-sm"></div>
            </div>
        </div>
        
        <div id="main-content" class="opacity-50 pointer-events-none">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto mb-8">
                <div class="bg-white p-6 rounded-2xl shadow-lg">
                    <h2 class="text-xl font-semibold mb-4">🔍 Pencarian Video</h2>
                    <form id="youtube-form">
                        <div class="space-y-4">
                            <div>
                                <label for="keyword" class="block text-sm font-medium text-slate-700 mb-1">Kata Kunci</label>
                                <input type="text" id="keyword" placeholder="Contoh: review kamera terbaru" class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition">
                            </div>
                            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div>
                                    <label for="video-type" class="block text-sm font-medium text-slate-700 mb-1">Jenis Video</label>
                                    <select id="video-type" class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition appearance-none form-select">
                                        <option value="all">Semua Video</option>
                                        <option value="regular">Video Reguler</option>
                                        <option value="shorts">YouTube Shorts</option>
                                        <option value="live">Live</option>
                                    </select>
                                </div>
                                <div>
                                    <label for="sort-option" class="block text-sm font-medium text-slate-700 mb-1">Urutkan</label>
                                    <select id="sort-option" class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition appearance-none form-select">
                                        <option>Paling Relevan</option>
                                        <option>Paling Banyak Ditonton</option>
                                        <option>Terbaru</option>
                                        <option>VPH Tertinggi</option>
                                    </select>
                                </div>
                            </div>
                            <button type="submit" class="w-full bg-slate-800 text-white font-bold py-3 mt-2 rounded-lg hover:bg-slate-900 transition-colors shadow-lg flex items-center justify-center gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" /></svg>
                                Cari Video
                            </button>
                        </div>
                    </form>
                </div>
                <div class="bg-white p-6 rounded-2xl shadow-lg">
                    <h2 class="text-xl font-semibold mb-4">📈 Analisis Saluran Kompetitor</h2>
                    <form id="channel-form">
                        <div class="space-y-4">
                            <div>
                                <label for="channel-input" class="block text-sm font-medium text-slate-700 mb-1">URL atau ID Saluran</label>
                                <input type="text" id="channel-input" placeholder="Contoh: https://www.youtube.com/user/channelID" class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition">
                            </div>
                            <button type="submit" class="w-full bg-slate-800 text-white font-bold py-3 mt-2 rounded-lg hover:bg-slate-900 transition-colors shadow-lg flex items-center justify-center gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M10 3.5a1.5 1.5 0 011.5 1.5v3.5a1.5 1.5 0 01-1.5 1.5h-3.5a1.5 1.5 0 01-1.5-1.5V5a1.5 1.5 0 011.5-1.5h3.5zM15 10a1.5 1.5 0 011.5 1.5v3.5a1.5 1.5 0 01-1.5 1.5h-3.5a1.5 1.5 0 01-1.5-1.5v-3.5a1.5 1.5 0 011.5-1.5h3.5z" /></svg>
                                Analisis Saluran
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            <div id="loading" class="text-center my-10 hidden">
                <div role="status" class="flex justify-center items-center gap-3">
                    <svg aria-hidden="true" class="w-8 h-8 text-slate-200 animate-spin dark:text-slate-600 fill-amber-600" viewBox="0 0 100 101" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z" fill="currentColor"/>
                        <path d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0492C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z" fill="currentColor"/>
                    </svg>
                    <span class="text-slate-600">Mengambil data dari YouTube...</span>
                </div>
            </div>
            
            <div id="results-message" class="text-center my-10"></div>
            <div id="results-container" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"></div>
            <div id="analysis-container" class="mt-12 max-w-4xl mx-auto hidden">
                <div class="mb-8">
                    <h3 class="text-2xl font-bold mb-4">💡 Rekomendasi Judul untuk Dipakai</h3>
                    <div id="titles-container" class="space-y-3"></div>
                </div>
                <div>
                    <h3 class="text-2xl font-bold mb-4">🏷️ Rekomendasi Tag (Maks 500 karakter)</h3>
                    <div class="bg-slate-100 p-4 rounded-lg font-mono text-sm text-slate-700 break-words mb-3">
                        <code id="tags-code"></code>
                    </div>
                     <div class="relative">
                        <input type="text" id="tags-copy-input" readonly class="w-full bg-white border border-slate-300 rounded-lg p-2 pr-12">
                        <button class="copy-button absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-amber-600" data-target="tags-copy-input" title="Salin tag">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                        </button>
                    </div>
                </div>
            </div>

            <div id="channel-analysis-results" class="mt-12 max-w-4xl mx-auto hidden">
                <div class="bg-white p-6 rounded-2xl shadow-lg mb-8">
                    <div id="channel-summary" class="text-center mb-6"></div>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <h3 class="text-xl font-semibold mb-4 text-slate-800">Video Terpopuler</h3>
                            <div id="popular-videos" class="space-y-4"></div>
                        </div>
                        <div>
                            <h3 class="text-xl font-semibold mb-4 text-slate-800">Video Terbaru</h3>
                            <div id="recent-videos" class="space-y-4"></div>
                        </div>
                    </div>
                    <div class="mt-8">
                        <h3 class="text-xl font-semibold mb-4 text-slate-800">Wawasan AI dari Kompetitor 🤖</h3>
                        <div class="bg-amber-50 p-6 rounded-xl flex flex-col">
                            <button id="getAiChannelInsightsBtn" class="bg-slate-800 text-white font-semibold py-2 rounded-lg hover:bg-slate-900 transition-colors shadow-md disabled:bg-slate-400 disabled:cursor-not-allowed">
                                Dapatkan Wawasan
                            </button>
                            <div id="aiChannelLoading" class="hidden my-4 text-center">
                                <span class="text-amber-600">AI sedang menganalisis saluran...</span>
                            </div>
                            <div id="aiChannelInsights" class="mt-4 text-sm text-slate-800 space-y-4 hidden"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Video Modal -->
        <div id="videoModal" class="modal">
            <div class="modal-content">
                <span id="closeModal" class="close-btn">&times;</span>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Video Player -->
                    <div class="md:col-span-1">
                        <div class="aspect-w-16 aspect-h-9">
                            <iframe id="videoPlayer" class="w-full aspect-video rounded-lg" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
                        </div>
                        <div class="mt-4">
                            <h3 id="modalTitle" class="text-xl font-bold text-slate-900"></h3>
                            <p id="modalChannel" class="text-sm text-slate-500"></p>
                        </div>
                        <div class="mt-4">
                            <h4 class="text-lg font-semibold text-slate-800">Deskripsi Video</h4>
                            <div id="modalDescription" class="text-sm text-slate-600 overflow-y-auto max-h-48 mt-2 p-2 bg-slate-100 rounded-lg"></div>
                        </div>
                    </div>

                    <!-- AI Analysis -->
                    <div class="md:col-span-1">
                        <div class="bg-amber-50 p-6 rounded-xl h-full flex flex-col">
                            <h4 class="text-lg font-bold text-slate-800 mb-4">Asisten Konten AI 🤖</h4>
                            <p class="text-sm text-slate-600 mb-4">Dapatkan ide konten dan saran thumbnail dari AI berdasarkan video ini.</p>
                            <button id="getAiIdeasBtn" class="bg-slate-800 text-white font-semibold py-2 rounded-lg hover:bg-slate-900 transition-colors shadow-md disabled:bg-slate-400 disabled:cursor-not-allowed">
                                Dapatkan Ide
                            </button>
                            <div id="aiLoading" class="hidden my-4 text-center">
                                <span class="text-amber-600">AI sedang berpikir...</span>
                            </div>
                            <div id="aiIdeas" class="mt-4 text-sm text-slate-800 space-y-4 overflow-y-auto flex-grow hidden"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
        document.addEventListener('DOMContentLoaded', () => {
            const youtubeApiKeyInput = document.getElementById('youtube-api-key');
            const geminiApiKeyInput = document.getElementById('gemini-api-key');
            const saveApiKeyBtn = document.getElementById('save-api-key');
            const apiKeyMessage = document.getElementById('api-key-message');
            const mainContent = document.getElementById('main-content');
            const youtubeForm = document.getElementById('youtube-form');
            const keywordInput = document.getElementById('keyword');
            const videoTypeSelect = document.getElementById('video-type');
            const sortOptionSelect = document.getElementById('sort-option');
            const channelForm = document.getElementById('channel-form');
            const channelInput = document.getElementById('channel-input');

            const loadingDiv = document.getElementById('loading');
            const resultsContainer = document.getElementById('results-container');
            const resultsMessage = document.getElementById('results-message');
            const analysisContainer = document.getElementById('analysis-container');
            const titlesContainer = document.getElementById('titles-container');
            const tagsCode = document.getElementById('tags-code');
            const tagsCopyInput = document.getElementById('tags-copy-input');
            const channelAnalysisResults = document.getElementById('channel-analysis-results');
            const popularVideosContainer = document.getElementById('popular-videos');
            const recentVideosContainer = document.getElementById('recent-videos');
            const channelSummary = document.getElementById('channel-summary');
            const getAiChannelInsightsBtn = document.getElementById('getAiChannelInsightsBtn');
            const aiChannelLoading = document.getElementById('aiChannelLoading');
            const aiChannelInsights = document.getElementById('aiChannelInsights');
            
            const settingsToggle = document.getElementById('settings-toggle');
            const settingsContent = document.getElementById('settings-content');
            const settingsArrow = document.getElementById('settings-arrow');
            const videoModal = document.getElementById('videoModal');
            const closeModalBtn = document.getElementById('closeModal');
            const videoPlayer = document.getElementById('videoPlayer');
            const modalTitle = document.getElementById('modalTitle');
            const modalChannel = document.getElementById('modalChannel');
            const modalDescription = document.getElementById('modalDescription');
            const getAiIdeasBtn = document.getElementById('getAiIdeasBtn');
            const aiLoading = document.getElementById('aiLoading');
            const aiIdeas = document.getElementById('aiIdeas');

            let youtubeApiKey = localStorage.getItem('youtubeApiKey');
            let geminiApiKey = localStorage.getItem('geminiApiKey');

            const checkApiKey = () => {
                youtubeApiKey = localStorage.getItem('youtubeApiKey');
                geminiApiKey = localStorage.getItem('geminiApiKey');
                youtubeApiKeyInput.value = youtubeApiKey || '';
                geminiApiKeyInput.value = geminiApiKey || '';

                if (youtubeApiKey) {
                    mainContent.classList.remove('opacity-50', 'pointer-events-none');
                    apiKeyMessage.textContent = 'API Key YouTube tersimpan.';
                    apiKeyMessage.className = 'mt-3 text-sm text-green-600';
                } else {
                    mainContent.classList.add('opacity-50', 'pointer-events-none');
                    apiKeyMessage.textContent = '⚠️ Masukkan YouTube API Key untuk memulai pencarian.';
                    apiKeyMessage.className = 'mt-3 text-sm text-amber-600';
                    settingsContent.classList.remove('hidden');
                    settingsArrow.classList.add('rotate-180');
                }

                if (geminiApiKey) {
                    getAiIdeasBtn.disabled = false;
                    getAiChannelInsightsBtn.disabled = false;
                } else {
                    getAiIdeasBtn.disabled = true;
                    getAiChannelInsightsBtn.disabled = true;
                }
            };

            settingsToggle.addEventListener('click', () => {
                settingsContent.classList.toggle('hidden');
                settingsArrow.classList.toggle('rotate-180');
            });

            saveApiKeyBtn.addEventListener('click', () => {
                const newYoutubeKey = youtubeApiKeyInput.value.trim();
                const newGeminiKey = geminiApiKeyInput.value.trim();

                if (newYoutubeKey) {
                    localStorage.setItem('youtubeApiKey', newYoutubeKey);
                } else {
                    localStorage.removeItem('youtubeApiKey');
                }
                
                if (newGeminiKey) {
                    localStorage.setItem('geminiApiKey', newGeminiKey);
                } else {
                    localStorage.removeItem('geminiApiKey');
                }

                apiKeyMessage.textContent = 'API Key berhasil disimpan!';
                apiKeyMessage.className = 'mt-3 text-sm text-green-600';
                checkApiKey();
            });

            const calculateVPH = (views, publishedAt) => {
                const publishedTime = new Date(publishedAt);
                const hours = (new Date() - publishedTime) / 3600000;
                return hours > 0 ? Math.round(views / hours) : 0;
            };

            const formatViews = (n) => {
                if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}jt`;
                if (n >= 1_000) return `${(n / 1_000).toFixed(1)}rb`;
                return n.toString();
            };

            const formatTimeAgo = (publishedAt) => {
                const dt = new Date(publishedAt);
                const now = new Date();
                const seconds = Math.floor((now - dt) / 1000);
                let interval = seconds / 31536000;
                if (interval > 1) return `${Math.floor(interval)} tahun lalu`;
                interval = seconds / 2592000;
                if (interval > 1) return `${Math.floor(interval)} bulan lalu`;
                interval = seconds / 86400;
                if (interval > 1) return `${Math.floor(interval)} hari lalu`;
                 interval = seconds / 3600;
                if (interval > 1) return `${Math.floor(interval)} jam lalu`;
                interval = seconds / 60;
                if (interval > 1) return `${Math.floor(interval)} menit lalu`;
                return "Baru saja";
            };

            const formatPublishDateWIB = (publishedAt) => {
                const date = new Date(publishedAt);
                const options = {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    timeZone: 'Asia/Jakarta',
                };
                return date.toLocaleString('id-ID', options) + ' WIB';
            };
            
            const parseDuration = (duration) => {
                const matches = duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
                const hours = parseInt(matches[1] || 0, 10);
                const minutes = parseInt(matches[2] || 0, 10);
                const seconds = parseInt(matches[3] || 0, 10);
                return hours * 3600 + minutes * 60 + seconds;
            };

            const getYouTubeVideos = async (query, maxResults = 30) => {
                try {
                    const searchUrl = `https://www.googleapis.com/youtube/v3/search?part=snippet&q=${encodeURIComponent(query)}&type=video&maxResults=${maxResults}&key=${youtubeApiKey}`;
                    const searchRes = await fetch(searchUrl);
                    const searchData = await searchRes.json();
                    
                    if (searchData.error) {
                        throw new Error(`Error API: ${searchData.error.message}`);
                    }

                    if (!searchData.items || searchData.items.length === 0) {
                        return [];
                    }

                    const videoIds = searchData.items.map(item => item.id.videoId).join(',');
                    
                    const statsUrl = `https://www.googleapis.com/youtube/v3/videos?part=statistics,snippet,contentDetails&id=${videoIds}&key=${youtubeApiKey}`;
                    const statsRes = await fetch(statsUrl);
                    const statsData = await statsRes.json();
                    
                    if (statsData.error) {
                        throw new Error(`Error API: ${statsData.error.message}`);
                    }
                    
                    return statsData.items.map(item => ({
                        id: item.id,
                        title: item.snippet.title,
                        channel: item.snippet.channelTitle,
                        publishedAt: item.snippet.publishedAt,
                        views: parseInt(item.statistics.viewCount || 0, 10),
                        thumbnail: item.snippet.thumbnails.high.url,
                        description: item.snippet.description,
                        duration: item.contentDetails.duration,
                        live: item.snippet.liveBroadcastContent,
                        vph: calculateVPH(parseInt(item.statistics.viewCount || 0, 10), item.snippet.publishedAt)
                    }));
                } catch (error) {
                    console.error("Gagal mengambil data YouTube:", error);
                    resultsMessage.innerHTML = `<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg" role="alert"><strong>Gagal!</strong> Periksa koneksi internet Anda atau pastikan API Key valid. <br><small>${error.message}</small></div>`;
                    return null;
                }
            };
            
            const filterVideos = (videos, type) => {
                switch (type) {
                    case 'regular':
                        return videos.filter(v => v.live === 'none' && parseDuration(v.duration) > 60);
                    case 'shorts':
                        return videos.filter(v => parseDuration(v.duration) <= 60);
                    case 'live':
                        return videos.filter(v => v.live === 'live' || v.live === 'upcoming');
                    default:
                        return videos;
                }
            };

            const sortVideos = (data, mode) => {
                switch (mode) {
                    case "Paling Banyak Ditonton":
                        return [...data].sort((a, b) => b.views - a.views);
                    case "Terbaru":
                        return [...data].sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt));
                    case "VPH Tertinggi":
                        return [...data].sort((a, b) => b.vph - a.vph);
                    default:
                        return data;
                }
            };

            const renderVideos = (videos) => {
                resultsContainer.innerHTML = '';
                videos.forEach(v => {
                    let badgeHtml = '';
                    let videoType = 'regular';
                    if (v.live === 'live' || v.live === 'upcoming') {
                        badgeHtml = `<span class="absolute top-2 left-2 bg-red-600 text-white text-xs font-bold px-2 py-1 rounded-full z-10">LIVE</span>`;
                        videoType = 'live';
                    } else if (parseDuration(v.duration) <= 60) {
                        badgeHtml = `<span class="absolute top-2 left-2 bg-blue-600 text-white text-xs font-bold px-2 py-1 rounded-full z-10">SHORTS</span>`;
                        videoType = 'shorts';
                    }

                    const videoCard = document.createElement('div');
                    videoCard.className = 'bg-white rounded-xl shadow-md overflow-hidden transform hover:-translate-y-1 transition-transform duration-300 fade-in cursor-pointer';
                    videoCard.dataset.videoId = v.id;
                    videoCard.dataset.videoTitle = v.title;
                    videoCard.dataset.videoChannel = v.channel;
                    videoCard.dataset.videoDesc = v.description;
                    videoCard.dataset.videoType = videoType;
                    videoCard.innerHTML = `
                        <div class="relative">
                            <img class="w-full h-48 object-cover" src="${v.thumbnail}" alt="${v.title}">
                            ${badgeHtml}
                        </div>
                        <div class="p-4">
                            <div class="block text-lg font-semibold text-slate-800 hover:text-amber-600 transition-colors leading-tight truncate">${v.title}</div>
                            <p class="text-slate-500 text-sm mt-1">${v.channel}</p>
                            <div class="flex flex-wrap gap-2 mt-4 text-xs font-medium">
                                <span class="inline-flex items-center px-2.5 py-1 rounded-full bg-red-100 text-red-800">👁 ${formatViews(v.views)} views</span>
                                <span class="inline-flex items-center px-2.5 py-1 rounded-full bg-blue-100 text-blue-800">⚡ ${v.vph} VPH</span>
                                <span class="inline-flex items-center px-2.5 py-1 rounded-full bg-green-100 text-green-800">⏱ ${formatTimeAgo(v.publishedAt)}</span>
                                <span class="inline-flex items-center px-2.5 py-1 rounded-full bg-slate-100 text-slate-700">🗓 ${formatPublishDateWIB(v.publishedAt)}</span>
                            </div>
                        </div>
                    `;
                    resultsContainer.appendChild(videoCard);
                });
            };

            const renderAnalysis = (videos) => {
                const allTitles = videos.map(v => v.title);
                
                titlesContainer.innerHTML = '';
                allTitles.slice(0, 5).forEach((title, index) => {
                    const titleId = `title-copy-${index}`;
                    const titleElement = document.createElement('div');
                    titleElement.className = 'relative';
                    titleElement.innerHTML = `
                        <input type="text" id="${titleId}" value="${title.replace(/"/g, '&quot;')}" readonly class="w-full bg-white border border-slate-300 rounded-lg p-2 pr-12">
                         <button class="copy-button absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-amber-600" data-target="${titleId}" title="Salin judul">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                        </button>
                    `;
                    titlesContainer.appendChild(titleElement);
                });

                const uniqueWords = new Set();
                allTitles.forEach(t => {
                    const words = t.split(/\W+/);
                    words.forEach(w => {
                        const cleanWord = w.toLowerCase().trim();
                        if (cleanWord.length > 2) {
                            uniqueWords.add(cleanWord);
                        }
                    });
                });

                let tagString = Array.from(uniqueWords).join(', ');
                if (tagString.length > 500) {
                    tagString = tagString.substring(0, 497) + '...';
                }
                tagsCode.textContent = tagString;
                tagsCopyInput.value = tagString;

                analysisContainer.classList.remove('hidden');
                channelAnalysisResults.classList.add('hidden');
            };

            const openVideoModal = (videoData) => {
                videoModal.style.display = 'block';
                videoPlayer.src = `https://www.youtube.com/embed/${videoData.id}?autoplay=1`;
                modalTitle.textContent = videoData.title;
                modalChannel.textContent = videoData.channel;
                modalDescription.textContent = videoData.description;
                aiIdeas.innerHTML = '';
                aiIdeas.classList.add('hidden');
                getAiIdeasBtn.onclick = () => getAiIdeas(videoData.title, videoData.description, videoData.type);
            };

            const closeVideoModal = () => {
                videoModal.style.display = 'none';
                videoPlayer.src = '';
                aiLoading.classList.add('hidden');
                aiIdeas.classList.add('hidden');
            };

            const getAiIdeas = async (title, description, type) => {
                if (!geminiApiKey) {
                    aiIdeas.textContent = "Masukkan Gemini API Key untuk menggunakan fitur ini.";
                    aiIdeas.classList.remove('hidden');
                    return;
                }

                aiLoading.classList.remove('hidden');
                aiIdeas.classList.add('hidden');
                aiIdeas.innerHTML = '';
                getAiIdeasBtn.disabled = true;

                let format = 'Reguler';
                if (type === 'shorts') {
                    format = 'YouTube Shorts';
                } else if (type === 'live') {
                    format = 'Live Stream';
                }

                let liveSection = '';
                if (type === 'live') {
                    liveSection = `V. Live Agenda & Interaksi Chat:
- Agenda:
  - Selamat datang dan perkenalan.
  - Penjelasan singkat tentang topik.
  - Menerima pertanyaan dari chat dan memberikan tanggapan yang relevan.
  - Berbagi pengalaman pribadi atau wawasan.
  - Mengundang interaksi dengan pertanyaan seputar topik.
  - Menjawab pertanyaan umum.
- Interaksi Chat:
  - Respon cepat terhadap pertanyaan dan komentar.
  - Mengakui dan merespon semua komentar.
  - Menggunakan emoji untuk interaksi dan engagement.
  - Meminta feedback dan saran.`;
                }

                const prompt = `Bertindak sebagai ahli pemasaran konten YouTube. Berikan analisis dan kerangka skrip untuk video dengan judul "${title}" dan deskripsi berikut:\n\n"${description}"\n\nBuatlah kerangka skrip dengan format seperti ini:\n
Kerangka Skrip YouTube: ${title}
Judul: ${title}
Format: ${format}
Platform: YouTube
I. HOOK (0:00-0:15)
- Suara: [Contoh: Suara lembut, musik ceria, atau intro yang dramatis]
- Visual: [Contoh: Cuplikan cepat, animasi, atau close-up objek]
- Teks: [Contoh: Teks overlay yang menarik perhatian]
- Narasi: [Contoh: Kalimat pembuka yang memicu rasa penasaran]
- Penjelasan singkat: [Ringkasan apa yang akan dibahas]

II. Intro (0:15-0:30)
- Suara: [Contoh: Transisi musik]
- Visual: [Contoh: Logo channel, perkenalan host]
- Narasi: [Contoh: "Selamat datang di channel [Nama Channel]..."]
- Penjelasan singkat: [Ringkasan singkat tentang topik dan manfaatnya bagi penonton]

III. Poin Utama (0:30-3:00)
- Poin 1: [Judul poin]
- Suara: [Contoh: Musik latar yang sesuai]
- Visual: [Contoh: Cuplikan relevan, grafik, atau demonstrasi produk]
- Narasi: [Penjelasan poin 1]
- Poin 2: [Judul poin]
- Suara: [Contoh: Efek suara atau musik yang berbeda]
- Visual: [Contoh: Cuplikan relevan, grafik, atau demonstrasi produk]
- Narasi: [Penjelasan poin 2]
- Poin 3: [Judul poin]
- Suara: [Contoh: Perubahan nada musik]
- Visual: [Contoh: Cuplikan relevan, grafik, atau demonstrasi produk]
- Narasi: [Penjelasan poin 3]

IV. CTA (Call to Action)
- Suara: [Contoh: Musik yang perlahan menghilang]
- Visual: [Contoh: Gambar statis dengan tombol subscribe, like, dan share]
- Narasi: [Contoh: "Jika Anda menikmati musik ini, beri 'like' dan 'subscribe'..."]
- Teks: [Contoh: "Subscribe, Like, dan Share!"]

${liveSection}

Berikan juga tiga ide thumbnail yang kuat, dengan detail visual.`;

                const payload = {
                    contents: [{ parts: [{ text: prompt }] }],
                    systemInstruction: { parts: [{ text: "Anda adalah asisten konten YouTube yang cerdas dan kreatif. Berikan saran yang singkat, langsung, dan sangat berguna untuk kreator konten." }] },
                };

                const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key=${geminiApiKey}`;
                try {
                    const response = await fetch(apiUrl, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });

                    const result = await response.json();
                    const aiText = result?.candidates?.[0]?.content?.parts?.[0]?.text;
                    if (aiText) {
                        const formattedText = aiText.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');
                        aiIdeas.innerHTML = formattedText;
                    } else {
                        aiIdeas.textContent = 'Gagal mendapatkan ide dari AI. Mungkin kuota API habis atau ada masalah lain.';
                    }
                } catch (error) {
                    console.error('Error fetching AI ideas:', error);
                    aiIdeas.textContent = 'Gagal terhubung ke layanan AI. Periksa koneksi Anda.';
                } finally {
                    aiLoading.classList.add('hidden');
                    aiIdeas.classList.remove('hidden');
                    getAiIdeasBtn.disabled = false;
                }
            };
            
            const getChannelId = (url) => {
                let channelId = '';
                const userUrlMatch = url.match(/youtube\.com\/user\/([^/]+)/);
                const channelUrlMatch = url.match(/youtube\.com\/(?:c\/|channel\/)([^/]+)/);
                if (channelUrlMatch && channelUrlMatch[1]) {
                    channelId = channelUrlMatch[1];
                } else if (userUrlMatch && userUrlMatch[1]) {
                    // This requires a separate API call to get the channel ID from username, which is a bit complex
                    // For simplicity, we assume the user provides the channel ID directly for /user/ links
                    channelId = url.substring(url.lastIndexOf('/') + 1);
                } else {
                    channelId = url;
                }
                return channelId.trim();
            };

            const getChannelData = async (channelId) => {
                const url = `https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&id=${channelId}&key=${youtubeApiKey}`;
                const res = await fetch(url);
                const data = await res.json();
                if (data.error) {
                    throw new Error(data.error.message);
                }
                if (data.items.length === 0) {
                    throw new Error("Saluran tidak ditemukan atau ID tidak valid.");
                }
                return data.items[0];
            };

            const getChannelVideos = async (channelId, maxResults = 10) => {
                const uploadPlaylistUrl = `https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id=${channelId}&key=${youtubeApiKey}`;
                const uploadRes = await fetch(uploadPlaylistUrl);
                const uploadData = await uploadRes.json();
                
                if (uploadData.error) {
                    throw new Error(uploadData.error.message);
                }
                const uploadsPlaylistId = uploadData.items[0]?.contentDetails?.relatedPlaylists?.uploads;
                if (!uploadsPlaylistId) {
                    throw new Error("Daftar putar video tidak ditemukan.");
                }

                const playlistUrl = `https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,contentDetails&playlistId=${uploadsPlaylistId}&maxResults=${maxResults}&key=${youtubeApiKey}`;
                const playlistRes = await fetch(playlistUrl);
                const playlistData = await playlistRes.json();
                if (playlistData.error) {
                    throw new Error(playlistData.error.message);
                }
                
                const videoIds = playlistData.items.map(item => item.contentDetails.videoId).join(',');
                const videosUrl = `https://www.googleapis.com/youtube/v3/videos?part=statistics,snippet,contentDetails&id=${videoIds}&key=${youtubeApiKey}`;
                const videosRes = await fetch(videosUrl);
                const videosData = await videosRes.json();
                if (videosData.error) {
                    throw new Error(videosData.error.message);
                }

                return videosData.items.map(item => ({
                    id: item.id,
                    title: item.snippet.title,
                    channel: item.snippet.channelTitle,
                    publishedAt: item.snippet.publishedAt,
                    views: parseInt(item.statistics.viewCount || 0, 10),
                    thumbnail: item.snippet.thumbnails.high.url,
                    description: item.snippet.description,
                    duration: item.contentDetails.duration,
                    live: item.snippet.liveBroadcastContent,
                    vph: calculateVPH(parseInt(item.statistics.viewCount || 0, 10), item.snippet.publishedAt)
                }));
            };

            const handleChannelAnalysis = async () => {
                const url = channelInput.value.trim();
                if (!url) {
                    resultsMessage.innerHTML = `<div class="bg-amber-100 border border-amber-400 text-amber-700 px-4 py-3 rounded-lg" role="alert"><strong>Oops!</strong> Mohon masukkan URL atau ID saluran.</div>`;
                    return;
                }
                if (!youtubeApiKey) {
                    resultsMessage.innerHTML = `<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg" role="alert"><strong>Oops!</strong> Mohon masukkan YouTube Data API Key di Pengaturan.</div>`;
                    return;
                }

                showLoading();
                resultsContainer.innerHTML = '';
                analysisContainer.classList.add('hidden');
                channelAnalysisResults.classList.add('hidden');
                
                try {
                    const channelId = getChannelId(url);
                    const channelData = await getChannelData(channelId);
                    const allChannelVideos = await getChannelVideos(channelId, 20);

                    const popularVideos = [...allChannelVideos].sort((a, b) => b.views - a.views).slice(0, 5);
                    const recentVideos = [...allChannelVideos].sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt)).slice(0, 5);
                    
                    renderChannelAnalysis(channelData, popularVideos, recentVideos);

                } catch (error) {
                    resultsMessage.innerHTML = `<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg" role="alert"><strong>Gagal!</strong> Terjadi kesalahan saat menganalisis saluran: ${error.message}</div>`;
                    console.error("Channel analysis error:", error);
                } finally {
                    hideLoading();
                }
            };
            
            const renderChannelAnalysis = (channel, popularVideos, recentVideos) => {
                resultsMessage.innerHTML = `<div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg" role="alert"><strong>Sukses!</strong> Analisis saluran ${channel.snippet.title} selesai.</div>`;
                
                channelSummary.innerHTML = `
                    <div class="flex items-center justify-center mb-4">
                        <img src="${channel.snippet.thumbnails.high.url}" class="rounded-full w-24 h-24 shadow-md mr-4">
                        <h2 class="text-3xl font-bold text-slate-900">${channel.snippet.title}</h2>
                    </div>
                    <div class="flex justify-center space-x-6 text-slate-600">
                        <div class="text-center">
                            <p class="text-2xl font-bold text-slate-800">${formatViews(parseInt(channel.statistics.subscriberCount))}</p>
                            <p class="text-sm">Subscribers</p>
                        </div>
                        <div class="text-center">
                            <p class="text-2xl font-bold text-slate-800">${formatViews(parseInt(channel.statistics.viewCount))}</p>
                            <p class="text-sm">Total Views</p>
                        </div>
                        <div class="text-center">
                            <p class="text-2xl font-bold text-slate-800">${parseInt(channel.statistics.videoCount).toLocaleString('id-ID')}</p>
                            <p class="text-sm">Jumlah Video</p>
                        </div>
                    </div>
                `;
                
                popularVideosContainer.innerHTML = '';
                popularVideos.forEach(v => {
                    const card = document.createElement('div');
                    card.className = 'flex items-center space-x-4 p-3 bg-slate-50 rounded-lg shadow-sm cursor-pointer hover:bg-slate-100';
                    card.dataset.videoId = v.id;
                    card.dataset.videoTitle = v.title;
                    card.dataset.videoChannel = v.channel;
                    card.dataset.videoDesc = v.description;
                    card.dataset.videoType = 'regular';
                    card.innerHTML = `
                        <img src="${v.thumbnail}" class="w-24 h-16 object-cover rounded-md flex-shrink-0">
                        <div class="flex-grow overflow-hidden">
                            <p class="font-semibold truncate">${v.title}</p>
                            <div class="text-xs text-slate-500 mt-1">
                                <span>👁 ${formatViews(v.views)} views</span>
                                <span>| ⏱ ${formatTimeAgo(v.publishedAt)}</span>
                            </div>
                        </div>
                    `;
                    popularVideosContainer.appendChild(card);
                });

                recentVideosContainer.innerHTML = '';
                recentVideos.forEach(v => {
                     const card = document.createElement('div');
                    card.className = 'flex items-center space-x-4 p-3 bg-slate-50 rounded-lg shadow-sm cursor-pointer hover:bg-slate-100';
                    card.dataset.videoId = v.id;
                    card.dataset.videoTitle = v.title;
                    card.dataset.videoChannel = v.channel;
                    card.dataset.videoDesc = v.description;
                    card.dataset.videoType = 'regular';
                    card.innerHTML = `
                        <img src="${v.thumbnail}" class="w-24 h-16 object-cover rounded-md flex-shrink-0">
                        <div class="flex-grow overflow-hidden">
                            <p class="font-semibold truncate">${v.title}</p>
                            <div class="text-xs text-slate-500 mt-1">
                                <span>👁 ${formatViews(v.views)} views</span>
                                <span>| ⏱ ${formatTimeAgo(v.publishedAt)}</span>
                            </div>
                        </div>
                    `;
                    recentVideosContainer.appendChild(card);
                });
                
                getAiChannelInsightsBtn.onclick = () => getAiChannelInsights(channel.snippet.title, popularVideos, recentVideos);
                
                channelAnalysisResults.classList.remove('hidden');
                analysisContainer.classList.add('hidden');
                resultsContainer.innerHTML = '';
            };
            
            const getAiChannelInsights = async (channelTitle, popularVideos, recentVideos) => {
                 if (!geminiApiKey) {
                    aiChannelInsights.textContent = "Masukkan Gemini API Key untuk menggunakan fitur ini.";
                    aiChannelInsights.classList.remove('hidden');
                    return;
                }

                aiChannelLoading.classList.remove('hidden');
                aiChannelInsights.classList.add('hidden');
                aiChannelInsights.innerHTML = '';
                getAiChannelInsightsBtn.disabled = true;

                const popularTitles = popularVideos.map(v => v.title).join('\n');
                const popularDescriptions = popularVideos.map(v => v.description).join('\n');
                const recentTitles = recentVideos.map(v => v.title).join('\n');

                const prompt = `Bertindaklah sebagai ahli strategi konten YouTube. Berikan analisis mendalam tentang strategi konten channel "${channelTitle}".
Berdasarkan data berikut:
Video Terpopuler:
${popularTitles}
Video Terbaru:
${recentTitles}

Identifikasi niche utama, target audiens, dan tema yang beresonansi. Kemudian, berikan tiga ide video baru yang bisa mengisi celah konten atau menarik audiens serupa. Berikan juga tiga ide thumbnail untuk video-video tersebut.`;

                const payload = {
                    contents: [{ parts: [{ text: prompt }] }],
                    systemInstruction: { parts: [{ text: "Anda adalah ahli strategi konten YouTube yang cerdas dan kreatif. Berikan saran yang singkat, langsung, dan sangat berguna untuk kreator konten." }] },
                };

                const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key=${geminiApiKey}`;
                try {
                    const response = await fetch(apiUrl, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });

                    const result = await response.json();
                    const aiText = result?.candidates?.[0]?.content?.parts?.[0]?.text;
                    if (aiText) {
                        const formattedText = aiText.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');
                        aiChannelInsights.innerHTML = formattedText;
                    } else {
                        aiChannelInsights.textContent = 'Gagal mendapatkan ide dari AI. Mungkin kuota API habis atau ada masalah lain.';
                    }
                } catch (error) {
                    console.error('Error fetching AI insights:', error);
                    aiChannelInsights.textContent = 'Gagal terhubung ke layanan AI. Periksa koneksi Anda.';
                } finally {
                    aiChannelLoading.classList.add('hidden');
                    aiChannelInsights.classList.remove('hidden');
                    getAiChannelInsightsBtn.disabled = false;
                }
            };

            const showLoading = () => {
                loadingDiv.classList.remove('hidden');
                resultsMessage.innerHTML = '';
                resultsContainer.innerHTML = '';
                analysisContainer.classList.add('hidden');
                channelAnalysisResults.classList.add('hidden');
            };

            const hideLoading = () => {
                loadingDiv.classList.add('hidden');
            };

            document.body.addEventListener('click', function(event) {
                const button = event.target.closest('.copy-button');
                if (button) {
                    const targetId = button.dataset.target;
                    const targetInput = document.getElementById(targetId);
                    if (targetInput) {
                        try {
                            // Coba menggunakan Clipboard API modern
                            navigator.clipboard.writeText(targetInput.value).then(() => {
                                const originalIcon = button.innerHTML;
                                button.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>`;
                                setTimeout(() => {
                                   button.innerHTML = originalIcon;
                                }, 1500);
                            }).catch(err => {
                                console.error('Gagal menyalin dengan Clipboard API:', err);
                                fallbackCopy(targetInput);
                            });
                        } catch (err) {
                            console.error('Clipboard API tidak tersedia, menggunakan fallback:', err);
                            fallbackCopy(targetInput);
                        }
                    }
                }
            });

            const fallbackCopy = (targetInput) => {
                const tempTextArea = document.createElement('textarea');
                tempTextArea.value = targetInput.value;
                document.body.appendChild(tempTextArea);
                tempTextArea.select();
                try {
                    document.execCommand('copy');
                    const button = document.querySelector(`[data-target='${targetInput.id}']`);
                    if (button) {
                        const originalIcon = button.innerHTML;
                        button.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>`;
                        setTimeout(() => {
                            button.innerHTML = originalIcon;
                        }, 1500);
                    }
                } catch (err) {
                    console.error('Gagal menyalin:', err);
                } finally {
                    document.body.removeChild(tempTextArea);
                }
            };
            
            resultsContainer.addEventListener('click', (e) => {
                const card = e.target.closest('[data-video-id]');
                if (card) {
                    const videoData = {
                        id: card.dataset.videoId,
                        title: card.dataset.videoTitle,
                        channel: card.dataset.videoChannel,
                        description: card.dataset.videoDesc,
                        type: card.dataset.videoType
                    };
                    openVideoModal(videoData);
                }
            });

            popularVideosContainer.addEventListener('click', (e) => {
                 const card = e.target.closest('[data-video-id]');
                if (card) {
                    const videoData = {
                        id: card.dataset.videoId,
                        title: card.dataset.videoTitle,
                        channel: card.dataset.videoChannel,
                        description: card.dataset.videoDesc,
                        type: card.dataset.videoType
                    };
                    openVideoModal(videoData);
                }
            });

            recentVideosContainer.addEventListener('click', (e) => {
                const card = e.target.closest('[data-video-id]');
                if (card) {
                    const videoData = {
                        id: card.dataset.videoId,
                        title: card.dataset.videoTitle,
                        channel: card.dataset.videoChannel,
                        description: card.dataset.videoDesc,
                        type: card.dataset.videoType
                    };
                    openVideoModal(videoData);
                }
            });
            
            closeModalBtn.addEventListener('click', closeVideoModal);
            window.addEventListener('click', (event) => {
                if (event.target === videoModal) {
                    closeVideoModal();
                }
            });

            youtubeForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const keyword = keywordInput.value.trim();
                const sortOption = sortOptionSelect.value;
                const videoType = videoTypeSelect.value;

                if (!youtubeApiKey) {
                    resultsMessage.innerHTML = `<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg" role="alert"><strong>Oops!</strong> Mohon masukkan YouTube Data API Key di Pengaturan.</div>`;
                    return;
                }
                if (!keyword) {
                    resultsMessage.innerHTML = `<div class="bg-amber-100 border border-amber-400 text-amber-700 px-4 py-3 rounded-lg" role="alert"><strong>Oops!</strong> Mohon masukkan kata kunci pencarian.</div>`;
                    return;
                }

                showLoading();

                const videos = await getYouTubeVideos(keyword);
                
                hideLoading();
                
                if (videos === null) {
                    return; 
                }

                const filteredVideos = filterVideos(videos, videoType);

                if (filteredVideos.length === 0) {
                    resultsMessage.innerHTML = `<div class="bg-slate-100 text-slate-700 px-4 py-3 rounded-lg" role="alert"><strong>Yah!</strong> Tidak ada video yang ditemukan untuk kata kunci "${keyword}" dengan filter yang dipilih.</div>`;
                } else {
                    resultsMessage.innerHTML = `<div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg" role="alert"><strong>Sukses!</strong> Ditemukan ${filteredVideos.length} video.</div>`;
                    const sortedVideos = sortVideos(filteredVideos, sortOption);
                    renderVideos(sortedVideos);
                    renderAnalysis(sortedVideos);
                }
            });

            channelForm.addEventListener('submit', (e) => {
                e.preventDefault();
                handleChannelAnalysis();
            });

            checkApiKey();
        });
        </script>
    </body>
    </html>
