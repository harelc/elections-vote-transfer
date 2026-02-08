/**
 * קולות נודדים - Interactive Sankey Diagram
 * Visualizes vote transfer between Israeli Knesset elections
 */

class VoteTransferSankey {
    constructor(containerId) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.tooltip = document.getElementById('tooltip');
        this.bottomSheet = document.getElementById('bottom-sheet');
        this.bottomSheetContent = document.getElementById('bottom-sheet-content');
        this.legendsOverlay = document.getElementById('legends-overlay');
        this.data = null;
        this.officialResults = null;
        this.currentTransition = '24_to_25';
        this.svg = null;
        this.g = null;
        this.percentMode = 'source'; // 'source' or 'target'

        this.margin = { top: 20, right: 100, bottom: 20, left: 100 };

        this.setupEventListeners();
        this.setupMobileListeners();

        // Listen for language changes
        window.addEventListener('langchange', () => {
            if (this.data) {
                this.updateInfo();
                this.render();
                this.updateLegend();
            }
        });

        // Load official results then initial data
        this.loadOfficialResults().then(() => {
            this.loadTransition(this.currentTransition);
        });
    }

    isMobile() {
        return window.innerWidth <= 768;
    }

    setupEventListeners() {
        // Navigation buttons
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const transition = btn.dataset.transition;
                this.loadTransition(transition);

                // Update active state
                document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        // Resize handler with debounce
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                if (this.data) {
                    this.render();
                }
            }, 250);
        });

        // Percent mode toggle (desktop)
        const toggleBtn = document.getElementById('percent-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.togglePercentMode());
        }

        // Export PNG button
        const exportBtn = document.getElementById('export-png');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportPNG());
        }
    }

    generateQRCodeDataURL() {
        // Pre-computed QR code for https://kolot-nodedim.netlify.app/
        const qrMatrix = [
            [1,1,1,1,1,1,1,0,1,0,0,0,1,1,1,0,0,0,1,1,1,1,1,1,1],
            [1,0,0,0,0,0,1,0,0,1,0,1,1,0,0,0,1,0,1,0,0,0,0,0,1],
            [1,0,1,1,1,0,1,0,1,1,0,0,0,1,1,0,1,0,1,0,1,1,1,0,1],
            [1,0,1,1,1,0,1,0,0,0,1,0,1,0,0,1,0,0,1,0,1,1,1,0,1],
            [1,0,1,1,1,0,1,0,1,0,1,1,0,0,1,1,1,0,1,0,1,1,1,0,1],
            [1,0,0,0,0,0,1,0,0,1,1,0,1,0,1,0,0,0,1,0,0,0,0,0,1],
            [1,1,1,1,1,1,1,0,1,0,1,0,1,0,1,0,1,0,1,1,1,1,1,1,1],
            [0,0,0,0,0,0,0,0,1,1,0,0,1,1,0,1,1,0,0,0,0,0,0,0,0],
            [1,0,1,1,0,1,1,1,1,0,1,0,0,0,1,0,0,1,1,0,0,1,0,1,0],
            [0,1,0,0,1,0,0,1,0,0,0,1,1,0,1,1,0,0,0,1,0,0,1,0,1],
            [1,1,0,1,0,0,1,0,0,1,0,1,0,1,0,0,1,1,0,0,1,0,0,1,0],
            [0,0,1,1,0,1,0,0,1,0,1,0,1,0,1,0,0,1,0,1,1,0,1,0,1],
            [0,0,0,1,1,0,1,0,1,1,0,0,1,1,0,1,1,0,1,0,0,1,1,0,0],
            [0,1,1,0,0,1,0,1,0,1,1,0,0,1,0,0,0,0,1,1,0,0,0,1,1],
            [1,0,1,0,1,0,1,0,1,0,0,1,0,1,1,0,1,1,0,1,1,0,1,0,0],
            [0,1,0,1,0,0,0,0,0,0,1,1,0,0,0,1,1,0,0,0,1,1,0,0,1],
            [1,0,0,1,1,1,1,0,1,1,1,0,1,1,1,0,0,1,1,1,1,1,0,1,0],
            [0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,1,0,0,0,1,0,0,1,1],
            [1,1,1,1,1,1,1,0,1,0,1,0,0,0,1,0,0,0,1,0,1,1,1,0,0],
            [1,0,0,0,0,0,1,0,0,0,0,0,1,1,0,0,1,0,0,0,1,0,1,0,1],
            [1,0,1,1,1,0,1,0,1,1,1,1,0,1,1,0,0,1,1,1,1,1,0,1,0],
            [1,0,1,1,1,0,1,0,0,1,0,0,1,0,1,0,1,0,0,1,0,0,0,0,1],
            [1,0,1,1,1,0,1,0,1,0,0,1,0,0,1,1,1,1,0,1,1,0,1,1,0],
            [1,0,0,0,0,0,1,0,0,0,1,1,0,0,0,1,0,0,0,1,1,0,0,1,1],
            [1,1,1,1,1,1,1,0,1,0,0,1,1,0,1,0,0,1,0,0,1,1,1,0,0]
        ];

        const size = 25;
        const cellSize = 4;
        const canvasSize = size * cellSize;
        const canvas = document.createElement('canvas');
        canvas.width = canvasSize;
        canvas.height = canvasSize;
        const ctx = canvas.getContext('2d');

        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, canvasSize, canvasSize);

        ctx.fillStyle = '#000000';
        for (let y = 0; y < size; y++) {
            for (let x = 0; x < size; x++) {
                if (qrMatrix[y][x]) {
                    ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
                }
            }
        }

        return canvas.toDataURL('image/png');
    }

    exportPNG() {
        const svgElement = this.container.querySelector('svg');
        if (!svgElement || !this.data) return;

        // Clone the SVG to avoid modifying the original
        const svgClone = svgElement.cloneNode(true);

        // Add background color
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('width', '100%');
        rect.setAttribute('height', '100%');
        rect.setAttribute('fill', '#1e1e2a');
        svgClone.insertBefore(rect, svgClone.firstChild);

        // Get SVG dimensions
        const svgWidth = parseInt(svgElement.getAttribute('width') || svgElement.clientWidth);
        const svgHeight = parseInt(svgElement.getAttribute('height') || svgElement.clientHeight);

        // Layout settings - simple header + chart + watermark (no extra legends needed)
        const headerHeight = 60;
        const watermarkHeight = 60;
        const scale = 2;
        const totalHeight = svgHeight + headerHeight + watermarkHeight;

        // Create canvas
        const canvas = document.createElement('canvas');
        canvas.width = svgWidth * scale;
        canvas.height = totalHeight * scale;
        const ctx = canvas.getContext('2d');
        ctx.scale(scale, scale);

        // Draw background for entire canvas
        ctx.fillStyle = '#0a0a0f';
        ctx.fillRect(0, 0, svgWidth, totalHeight);

        // Draw header with election info
        ctx.fillStyle = '#12121a';
        ctx.fillRect(0, 0, svgWidth, headerHeight);

        ctx.fillStyle = '#f8fafc';
        ctx.font = 'bold 18px Heebo, sans-serif';
        ctx.textAlign = 'center';
        const fromName = i18n.electionName(this.data.from_election);
        const toName = i18n.electionName(this.data.to_election);
        const headerLabel = i18n.getLang() === 'en'
            ? `Vote Transfer: ${fromName} → ${toName}`
            : `מעבר קולות: ${fromName} ← ${toName}`;
        ctx.fillText(headerLabel, svgWidth / 2, 28);

        // Stats line
        ctx.fillStyle = '#94a3b8';
        ctx.font = '12px Heebo, sans-serif';
        ctx.fillText(`${i18n.t('common_precincts')}: ${i18n.fmtNum(this.data.stats.common_precincts)} | ${i18n.t('r_squared')}: ${this.data.stats.r_squared.toFixed(3)}`, svgWidth / 2, 50);

        // Draw chart area background
        ctx.fillStyle = '#1e1e2a';
        ctx.fillRect(0, headerHeight, svgWidth, svgHeight);

        // Serialize and draw SVG
        const svgData = new XMLSerializer().serializeToString(svgClone);
        const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
        const url = URL.createObjectURL(svgBlob);

        const img = new Image();
        img.onload = () => {
            ctx.drawImage(img, 0, headerHeight);
            URL.revokeObjectURL(url);

            // Draw watermark section
            const watermarkY = totalHeight - watermarkHeight;
            ctx.fillStyle = '#1a1a25';
            ctx.fillRect(0, watermarkY, svgWidth, watermarkHeight);

            // Draw separator line
            ctx.strokeStyle = '#2a2a3a';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(0, watermarkY);
            ctx.lineTo(svgWidth, watermarkY);
            ctx.stroke();

            // Draw QR code
            const qrDataURL = this.generateQRCodeDataURL();
            const qrImg = new Image();
            qrImg.onload = () => {
                const qrSize = 45;
                ctx.drawImage(qrImg, 15, watermarkY + 7, qrSize, qrSize);

                // Draw watermark text
                ctx.fillStyle = '#f8fafc';
                ctx.font = 'bold 14px Heebo, sans-serif';
                ctx.textAlign = 'right';
                ctx.fillText(i18n.t('watermark_created'), svgWidth - 15, watermarkY + 25);

                ctx.fillStyle = '#64748b';
                ctx.font = '12px Heebo, sans-serif';
                ctx.fillText('https://kolot-nodedim.netlify.app/', svgWidth - 15, watermarkY + 45);

                // Download
                const link = document.createElement('a');
                link.download = `sankey-${this.currentTransition}.png`;
                link.href = canvas.toDataURL('image/png');
                link.click();
            };
            qrImg.src = qrDataURL;
        };
        img.src = url;
    }

    async loadOfficialResults() {
        try {
            const response = await fetch('/data/wiki_official_results.json');
            if (response.ok) {
                this.officialResults = await response.json();
                console.log('Official results loaded:', this.officialResults);
            }
        } catch (error) {
            console.warn('Could not load official results:', error);
        }
    }

    setupMobileListeners() {
        // Mobile percent toggle
        const mobileToggle = document.getElementById('mobile-percent-toggle');
        if (mobileToggle) {
            mobileToggle.addEventListener('click', () => this.togglePercentMode());
        }

        // Show legends button
        const showLegendsBtn = document.getElementById('show-legends-btn');
        if (showLegendsBtn) {
            showLegendsBtn.addEventListener('click', () => this.showLegendsOverlay());
        }

        // Close legends button
        const closeLegendsBtn = document.getElementById('close-legends');
        if (closeLegendsBtn) {
            closeLegendsBtn.addEventListener('click', () => this.hideLegendsOverlay());
        }

        // Close legends on overlay background click
        if (this.legendsOverlay) {
            this.legendsOverlay.addEventListener('click', (e) => {
                if (e.target === this.legendsOverlay) {
                    this.hideLegendsOverlay();
                }
            });
        }

        // Close bottom sheet on handle click
        if (this.bottomSheet) {
            this.bottomSheet.addEventListener('click', (e) => {
                if (e.target.classList.contains('bottom-sheet-handle')) {
                    this.hideBottomSheet();
                }
            });
        }

        // Close bottom sheet when clicking outside (on the chart area)
        document.addEventListener('click', (e) => {
            if (this.bottomSheet && this.bottomSheet.classList.contains('visible')) {
                const isClickInSheet = this.bottomSheet.contains(e.target);
                const isClickOnLink = e.target.classList.contains('sankey-link');
                if (!isClickInSheet && !isClickOnLink) {
                    this.hideBottomSheet();
                }
            }
        });
    }

    togglePercentMode() {
        this.percentMode = this.percentMode === 'source' ? 'target' : 'source';
        const isSource = this.percentMode === 'source';

        // Update desktop toggle
        const toggleValue = document.getElementById('toggle-value');
        if (toggleValue) {
            toggleValue.textContent = i18n.t(isSource ? 'pct_from_prev' : 'pct_from_next');
        }

        // Update mobile toggle
        const mobileToggleValue = document.getElementById('mobile-toggle-value');
        if (mobileToggleValue) {
            mobileToggleValue.textContent = i18n.t(isSource ? 'pct_prev_short' : 'pct_next_short');
        }
    }

    showBottomSheet(link) {
        if (!this.bottomSheet || !this.bottomSheetContent) return;

        const reversePercent = link.target.votes > 0
            ? ((link.value / link.target.votes) * 100).toFixed(1)
            : 0;

        const isSource = this.percentMode === 'source';
        const percent = isSource ? link.percentage : reversePercent;
        const srcName = i18n.partyName(link.sourceName);
        const tgtName = i18n.partyName(link.targetName);
        const description = isSource
            ? i18n.t('from_votes_of', { party: srcName })
            : i18n.t('from_votes_of_new', { party: tgtName });

        this.bottomSheetContent.innerHTML = `
            <div class="sheet-parties">
                <span class="sheet-party">
                    <span class="sheet-party-color" style="background: ${link.source.color}"></span>
                    ${srcName}
                </span>
                <span class="sheet-arrow">←</span>
                <span class="sheet-party">
                    <span class="sheet-party-color" style="background: ${link.target.color}"></span>
                    ${tgtName}
                </span>
            </div>
            <div class="sheet-percent">${percent}%</div>
            <div class="sheet-description">${description}</div>
            <div class="sheet-votes">${i18n.t('votes_from_common', { n: i18n.fmtNum(link.value) })}</div>
        `;

        this.bottomSheet.classList.add('visible');
    }

    hideBottomSheet() {
        if (this.bottomSheet) {
            this.bottomSheet.classList.remove('visible');
        }
    }

    showPartyBottomSheet(node) {
        if (!this.bottomSheet || !this.bottomSheetContent) return;

        const info = node.info || {};
        const electionType = node.side === 'from' ? i18n.t('in_prev_election') : i18n.t('in_new_election');
        const pName = i18n.partyName(node);
        const lName = i18n.leaderName(info);

        this.bottomSheetContent.innerHTML = `
            <div class="sheet-party-details">
                <div class="sheet-party-header">
                    <span class="sheet-party-color" style="background: ${node.color}"></span>
                    <span class="sheet-party-name">${pName}</span>
                </div>
                <div class="sheet-party-votes">${i18n.fmtNum(node.votes)} ${i18n.t('votes')} ${electionType}</div>
                ${node.seats ? `<div class="sheet-party-seats">${node.seats} ${i18n.t('seats')}</div>` : ''}
                ${lName ? `
                    <div class="sheet-party-leader">
                        ${info.leader_image ? `<img class="sheet-leader-img" src="${info.leader_image}" alt="${lName}" onerror="this.style.display='none'">` : ''}
                        <div class="sheet-leader-info">
                            <span class="sheet-leader-label">${i18n.t('leader_label')}</span>
                            <span class="sheet-leader-name">${lName}</span>
                        </div>
                    </div>
                ` : ''}
                ${info.ideology ? `<div class="sheet-party-ideology">${info.ideology}</div>` : ''}
                ${info.description ? `<div class="sheet-party-description">${info.description}</div>` : ''}
            </div>
        `;

        this.bottomSheet.classList.add('visible');
    }

    showLegendsOverlay() {
        if (!this.legendsOverlay || !this.data) return;

        // Populate from list
        const fromList = document.getElementById('overlay-from-list');
        const toList = document.getElementById('overlay-to-list');
        const fromTitle = document.getElementById('overlay-from-title');
        const toTitle = document.getElementById('overlay-to-title');

        if (fromTitle) fromTitle.textContent = i18n.electionName(this.data.from_election);
        if (toTitle) toTitle.textContent = i18n.electionName(this.data.to_election);

        if (fromList) {
            fromList.innerHTML = this.data.nodes_from
                .sort((a, b) => b.votes - a.votes)
                .map(p => this.createLegendRowHTML(p))
                .join('');
            this.setupLegendRowListeners(fromList);
        }

        if (toList) {
            toList.innerHTML = this.data.nodes_to
                .sort((a, b) => b.votes - a.votes)
                .map(p => this.createLegendRowHTML(p))
                .join('');
            this.setupLegendRowListeners(toList);
        }

        this.legendsOverlay.classList.add('visible');
    }

    createLegendRowHTML(party) {
        const info = party.info || {};
        const hasDetails = info.leader || info.ideology || info.description;

        let detailsHTML = '';
        if (hasDetails) {
            detailsHTML = `
                <div class="legend-row-details">
                    ${info.leader ? `
                        <div class="legend-row-leader">
                            ${info.leader_image ? `<img class="legend-row-leader-img" src="${info.leader_image}" alt="${info.leader}" onerror="this.style.display='none'">` : ''}
                            <span class="legend-row-leader-name">${info.leader}</span>
                        </div>
                    ` : ''}
                    ${info.ideology ? `<div class="legend-row-ideology">${info.ideology}</div>` : ''}
                    ${info.description ? `<div class="legend-row-description">${info.description}</div>` : ''}
                </div>
            `;
        }

        return `
            <div class="legend-row" ${hasDetails ? 'data-expandable="true"' : ''}>
                <div class="legend-row-main">
                    <span class="legend-row-color" style="background: ${party.color}"></span>
                    <span class="legend-row-name">${i18n.partyName(party)}</span>
                    <span class="legend-row-votes">${i18n.fmtNum(party.votes)}</span>
                    ${hasDetails ? '<span class="legend-row-chevron">▼</span>' : ''}
                </div>
                ${detailsHTML}
            </div>
        `;
    }

    setupLegendRowListeners(container) {
        container.querySelectorAll('.legend-row[data-expandable]').forEach(row => {
            row.addEventListener('click', () => {
                row.classList.toggle('expanded');
            });
        });
    }

    hideLegendsOverlay() {
        if (this.legendsOverlay) {
            this.legendsOverlay.classList.remove('visible');
        }
    }

    async loadTransition(transitionId) {
        this.currentTransition = transitionId;
        this.container.innerHTML = `<div class="loading">${i18n.t('loading')}</div>`;

        try {
            const url = `/data/transfer_${transitionId}.json`;
            console.log('Fetching:', url);

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.data = await response.json();
            console.log('Data loaded:', this.data);

            this.updateInfo();
            this.render();
            this.updateLegend();
        } catch (error) {
            console.error('Error loading data:', error);
            this.container.innerHTML = `<div class="loading">${i18n.t('error_loading')}: ${error.message}</div>`;
        }
    }

    updateInfo() {
        const { from_election, to_election, stats } = this.data;

        // Update election info
        document.getElementById('from-election-name').textContent = i18n.electionName(from_election);
        document.getElementById('from-election-date').textContent = this.formatDate(from_election.date);
        document.getElementById('to-election-name').textContent = i18n.electionName(to_election);
        document.getElementById('to-election-date').textContent = this.formatDate(to_election.date);

        // Update voter statistics for "from" election
        if (from_election.eligible_voters) {
            document.getElementById('from-eligible').textContent = i18n.fmtNum(from_election.eligible_voters);
            document.getElementById('from-votes').textContent = i18n.fmtNum(from_election.votes_cast);
            document.getElementById('from-turnout').textContent = from_election.turnout_percent.toFixed(1) + '%';
        }

        // Update voter statistics for "to" election
        if (to_election.eligible_voters) {
            document.getElementById('to-eligible').textContent = i18n.fmtNum(to_election.eligible_voters);
            document.getElementById('to-votes').textContent = i18n.fmtNum(to_election.votes_cast);
            document.getElementById('to-turnout').textContent = to_election.turnout_percent.toFixed(1) + '%';
        }

        // Update stats
        document.getElementById('stat-precincts').textContent = i18n.fmtNum(stats.common_precincts);
        document.getElementById('stat-r2').textContent = stats.r_squared.toFixed(3);
    }

    formatDate(dateStr) {
        const date = new Date(dateStr);
        const locale = i18n.getLang() === 'he' ? 'he-IL' : 'en-GB';
        return date.toLocaleDateString(locale, { day: '2-digit', month: '2-digit', year: 'numeric' });
    }

    render() {
        if (!this.data) return;

        // Clear container
        this.container.innerHTML = '';

        // Get dimensions
        const rect = this.container.getBoundingClientRect();
        const width = rect.width || 800;
        const height = rect.height || 600;

        // Use smaller margins on mobile
        const margin = this.isMobile()
            ? { top: 10, right: 50, bottom: 10, left: 50 }
            : this.margin;

        const innerWidth = width - margin.left - margin.right;
        const innerHeight = height - margin.top - margin.bottom;

        console.log('Rendering with dimensions:', width, height, 'mobile:', this.isMobile());

        // Create SVG
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        this.g = this.svg.append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        const { nodes_from, nodes_to, transfers } = this.data;

        // Build nodes array
        const nodes = [
            ...nodes_from.map((n, i) => ({ ...n, id: `from_${i}`, side: 'from' })),
            ...nodes_to.map((n, i) => ({ ...n, id: `to_${i}`, side: 'to' }))
        ];

        // Create node index map
        const nodeIndex = {};
        nodes.forEach((n, i) => {
            nodeIndex[n.name + '_' + n.side] = i;
        });

        // Build links array - use node IDs for source/target
        const links = transfers
            .map(t => {
                const sourceIdx = nodeIndex[t.source + '_from'];
                const targetIdx = nodeIndex[t.target + '_to'];
                if (sourceIdx === undefined || targetIdx === undefined) {
                    console.warn('Missing node for transfer:', t.source, '->', t.target);
                    return null;
                }
                return {
                    source: nodes[sourceIdx].id,
                    target: nodes[targetIdx].id,
                    value: t.votes,
                    percentage: t.percentage,
                    sourceName: t.source,
                    targetName: t.target,
                    sourceSymbol: t.source_symbol,
                    targetSymbol: t.target_symbol
                };
            })
            .filter(l => l !== null && l.value > 0);

        console.log('Nodes:', nodes.length, 'Links:', links.length);

        if (links.length === 0) {
            this.container.innerHTML = `<div class="loading">${i18n.t('no_data')}</div>`;
            return;
        }

        // Create sankey generator - RTL layout (from=right, to=left)
        const sankeyGenerator = d3.sankey()
            .nodeId(d => d.id)
            .nodeWidth(20)
            .nodePadding(12)
            .nodeAlign(d3.sankeyJustify)
            .extent([[0, 0], [innerWidth, innerHeight]]);

        // We'll flip X coordinates after layout to achieve RTL

        // Generate layout
        const graph = sankeyGenerator({
            nodes: nodes.map(d => Object.assign({}, d)),
            links: links.map(d => Object.assign({}, d))
        });

        // Flip X coordinates for RTL layout (from on right, to on left)
        graph.nodes.forEach(node => {
            const newX0 = innerWidth - node.x1;
            const newX1 = innerWidth - node.x0;
            node.x0 = newX0;
            node.x1 = newX1;
        });

        // Create groups
        const linksGroup = this.g.append('g').attr('class', 'sankey-links');
        const nodesGroup = this.g.append('g').attr('class', 'sankey-nodes');

        // Draw links
        this.links = linksGroup.selectAll('.sankey-link')
            .data(graph.links)
            .join('path')
            .attr('class', 'sankey-link')
            .attr('d', d3.sankeyLinkHorizontal())
            .attr('stroke', d => d.target.color || '#6b7280')
            .attr('stroke-width', d => Math.max(1, d.width))
            .style('fill', 'none')
            .style('stroke-opacity', 0.4)
            .style('cursor', 'pointer')
            .on('mouseenter', (event, d) => {
                if (!this.isMobile()) {
                    this.showLinkTooltip(event, d);
                }
                d3.select(event.currentTarget).style('stroke-opacity', 0.7);
            })
            .on('mousemove', (event) => {
                if (!this.isMobile()) {
                    this.moveTooltip(event);
                }
            })
            .on('mouseleave', (event) => {
                if (!this.isMobile()) {
                    this.hideTooltip();
                }
                d3.select(event.currentTarget).style('stroke-opacity', 0.4);
            })
            .on('click', (event, d) => {
                if (this.isMobile()) {
                    this.showBottomSheet(d);
                }
            });

        // Draw nodes
        this.nodes = nodesGroup.selectAll('.sankey-node')
            .data(graph.nodes)
            .join('g')
            .attr('class', 'sankey-node')
            .attr('transform', d => `translate(${d.x0},${d.y0})`)
            .style('cursor', 'pointer')
            .on('mouseenter', (event, d) => {
                this.highlightNode(d);
                if (!this.isMobile()) {
                    this.showNodeTooltip(event, d);
                }
            })
            .on('mousemove', (event) => {
                if (!this.isMobile()) {
                    this.moveTooltip(event);
                }
            })
            .on('mouseleave', () => {
                this.unhighlightAll();
                if (!this.isMobile()) {
                    this.hideTooltip();
                }
            });

        // Node rectangles
        this.nodes.append('rect')
            .attr('height', d => Math.max(1, d.y1 - d.y0))
            .attr('width', d => d.x1 - d.x0)
            .attr('fill', d => d.color || '#6b7280')
            .attr('rx', 4)
            .attr('ry', 4)
            .style('cursor', 'pointer');

        // Node labels - RTL: from nodes on right (label on right), to nodes on left (label on left)
        this.nodes.append('text')
            .attr('x', d => d.side === 'from' ? (d.x1 - d.x0) + 6 : -6)
            .attr('y', d => (d.y1 - d.y0) / 2)
            .attr('dy', '0.35em')
            .attr('text-anchor', d => d.side === 'from' ? 'start' : 'end')
            .text(d => i18n.partyName(d))
            .style('font-size', this.isMobile() ? '10px' : '13px')
            .style('font-weight', '500')
            .style('fill', '#f0f0f5')
            .style('pointer-events', 'none');

        // Mobile info buttons
        if (this.isMobile()) {
            const infoButtons = this.nodes.append('g')
                .attr('class', 'node-info-btn')
                .attr('transform', d => {
                    const x = d.side === 'from' ? (d.x1 - d.x0) + 6 : -18;
                    const y = -8;
                    return `translate(${x}, ${y})`;
                })
                .style('cursor', 'pointer')
                .on('click', (event, d) => {
                    event.stopPropagation();
                    this.showPartyBottomSheet(d);
                });

            infoButtons.append('circle')
                .attr('r', 8)
                .attr('fill', 'var(--bg-tertiary)')
                .attr('stroke', 'var(--border-light)')
                .attr('stroke-width', 1);

            infoButtons.append('text')
                .attr('text-anchor', 'middle')
                .attr('dy', '0.35em')
                .attr('fill', 'var(--text-secondary)')
                .attr('font-size', '10px')
                .attr('font-weight', '600')
                .text('i');
        }

        console.log('Render complete');
    }

    highlightNode(node) {
        const connectedLinks = new Set();
        const connectedNodes = new Set([node.id]);

        this.links.each(function(d) {
            if (d.source.id === node.id || d.target.id === node.id) {
                connectedLinks.add(this);
                connectedNodes.add(d.source.id);
                connectedNodes.add(d.target.id);
            }
        });

        this.links
            .style('stroke-opacity', function(d) {
                return connectedLinks.has(this) ? 0.7 : 0.1;
            });

        this.nodes.style('opacity', d => connectedNodes.has(d.id) ? 1 : 0.3);
    }

    unhighlightAll() {
        this.links.style('stroke-opacity', 0.4);
        this.nodes.style('opacity', 1);
    }

    showNodeTooltip(event, node) {
        const info = node.info || {};
        const lName = i18n.leaderName(info);

        let html = `
            <div class="tooltip-header">
                <div class="tooltip-color" style="background-color: ${node.color}"></div>
                <span class="tooltip-title">${i18n.partyName(node)}</span>
                <span class="tooltip-symbol">(${node.symbol})</span>
            </div>
            <div class="tooltip-body">
                <div class="tooltip-stat">
                    <span class="tooltip-stat-label">${i18n.t('total_votes')}</span>
                    <span class="tooltip-stat-value">${i18n.fmtNum(node.votes)}</span>
                </div>
                ${lName ? `
                <div class="tooltip-stat">
                    <span class="tooltip-stat-label">${i18n.t('leader_label')}</span>
                    <span class="tooltip-stat-value">${lName}</span>
                </div>
                ` : ''}
                ${info.description ? `
                <div class="tooltip-description">${info.description}</div>
                ` : ''}
            </div>
        `;

        this.tooltip.innerHTML = html;
        this.tooltip.classList.add('visible');
        this.moveTooltip(event);
    }

    showLinkTooltip(event, link) {
        // Calculate reverse percentage (what % of target's votes came from source)
        const reversePercent = link.target.votes > 0
            ? ((link.value / link.target.votes) * 100).toFixed(1)
            : 0;

        const srcName = i18n.partyName(link.sourceName);
        const tgtName = i18n.partyName(link.targetName);
        const percentText = this.percentMode === 'source'
            ? `${link.percentage}% ${i18n.t('from_votes_of', { party: srcName })}`
            : `${reversePercent}% ${i18n.t('from_votes_of_new', { party: tgtName })}`;

        const html = `
            <div class="tooltip-flow">
                <div class="tooltip-flow-parties">
                    <span class="tooltip-flow-party">${srcName}</span>
                    <span class="tooltip-flow-arrow">←</span>
                    <span class="tooltip-flow-party">${tgtName}</span>
                </div>
                <div class="tooltip-flow-value">${percentText}</div>
                <div class="tooltip-flow-note">${i18n.t('votes_from_common_only', { n: i18n.fmtNum(link.value) })}</div>
            </div>
        `;

        this.tooltip.innerHTML = html;
        this.tooltip.classList.add('visible');
        this.moveTooltip(event);
    }

    moveTooltip(event) {
        const tooltipRect = this.tooltip.getBoundingClientRect();

        // RTL: prefer placing tooltip to the left of cursor
        let x = event.clientX - tooltipRect.width - 15;
        let y = event.clientY - 10;

        // If overflows left, place to the right
        if (x < 20) {
            x = event.clientX + 15;
        }
        // If still overflows right, clamp to right edge
        if (x + tooltipRect.width > window.innerWidth - 20) {
            x = window.innerWidth - tooltipRect.width - 20;
        }
        if (y + tooltipRect.height > window.innerHeight - 20) {
            y = window.innerHeight - tooltipRect.height - 20;
        }
        if (y < 20) y = 20;

        this.tooltip.style.left = `${x}px`;
        this.tooltip.style.top = `${y}px`;
    }

    hideTooltip() {
        this.tooltip.classList.remove('visible');
    }

    updateLegend() {
        // Get election IDs from current transition
        const [fromId, toId] = this.currentTransition.split('_to_');

        // Get official results if available
        const fromOfficial = this.officialResults ? this.officialResults[fromId] : null;
        const toOfficial = this.officialResults ? this.officialResults[toId] : null;

        // Update "from" legend (older election) - use official results
        this.updateLegendPanel(
            'legend-from',
            'legend-from-title',
            fromOfficial || this.data.nodes_from,
            this.data.from_election.name,
            'from',
            this.data.nodes_from // for color lookup
        );

        // Update "to" legend (newer election) - use official results
        this.updateLegendPanel(
            'legend-to',
            'legend-to-title',
            toOfficial || this.data.nodes_to,
            this.data.to_election.name,
            'to',
            this.data.nodes_to // for color lookup
        );
    }

    updateLegendPanel(legendId, titleId, parties, electionName, side, sankeyNodes) {
        const legend = document.getElementById(legendId);
        const title = document.getElementById(titleId);

        if (!legend) return;

        legend.innerHTML = '';

        // Update title
        if (title) {
            const num = electionName.replace('הכנסת ה-', '');
            title.textContent = i18n.t('official_results', { n: num });
        }

        // Create a color lookup from sankey nodes
        const colorMap = {};
        if (sankeyNodes) {
            sankeyNodes.forEach(n => {
                colorMap[n.name] = n.color;
            });
        }

        // Sort by votes descending
        const sortedParties = [...parties].sort((a, b) => b.votes - a.votes);

        sortedParties.forEach(party => {
            const item = document.createElement('div');
            item.className = 'legend-item';
            if (party.seats === 0) {
                item.classList.add('below-threshold');
            }

            // Get color from sankey nodes or use default
            const color = party.color || colorMap[party.name] || '#6b7280';
            const seatsText = party.seats > 0
                ? `<span class="legend-seats">${party.seats} ${i18n.t('seats')}</span>`
                : `<span class="legend-seats below">${i18n.t('below_threshold')}</span>`;

            item.innerHTML = `
                <div class="legend-color" style="background-color: ${color}"></div>
                <span class="legend-name">${i18n.partyName(party)}</span>
                <span class="legend-votes">${i18n.fmtNum(party.votes)} ${i18n.t('votes')}</span>
                ${seatsText}
            `;

            item.addEventListener('mouseenter', (event) => {
                if (this.nodes) {
                    this.nodes.each((d) => {
                        if (d.name === party.name && d.side === side) {
                            this.highlightNode(d);
                        }
                    });
                }
                // Use sankey node data for tooltip if available
                const sankeyParty = sankeyNodes?.find(n => n.name === party.name) || party;
                this.showPartyTooltip(event, { ...sankeyParty, votes: party.votes, seats: party.seats });
            });

            item.addEventListener('mousemove', (event) => this.moveTooltip(event));

            item.addEventListener('mouseleave', () => {
                this.unhighlightAll();
                this.hideTooltip();
            });

            legend.appendChild(item);
        });
    }

    showPartyTooltip(event, party) {
        const info = party.info || {};
        const pName = i18n.partyName(party);
        const lName = i18n.leaderName(info);
        // Show both Hebrew and English names in tooltip
        const altName = i18n.getLang() === 'he' ? (info.name_en || '') : (party.name || '');

        let html = `
            <div class="tooltip-party">
                <div class="tooltip-party-header">
                    ${info.logo ? `<img class="tooltip-logo" src="${info.logo}" alt="${pName}" onerror="this.style.display='none'">` : ''}
                    <div class="tooltip-party-title">
                        <span class="tooltip-party-name">${pName}</span>
                        ${altName ? `<span class="tooltip-party-name-en">${altName}</span>` : ''}
                    </div>
                </div>
                ${info.leader_image ? `
                <div class="tooltip-leader">
                    <img class="tooltip-leader-image" src="${info.leader_image}" alt="${lName}" onerror="this.style.display='none'">
                    <div class="tooltip-leader-info">
                        <span class="tooltip-leader-label">${i18n.t('leader_label')}</span>
                        <span class="tooltip-leader-name">${lName}</span>
                    </div>
                </div>
                ` : (lName ? `
                <div class="tooltip-stat">
                    <span class="tooltip-stat-label">${i18n.t('leader_label')}</span>
                    <span class="tooltip-stat-value">${lName}</span>
                </div>
                ` : '')}
                <div class="tooltip-stat">
                    <span class="tooltip-stat-label">${i18n.t('total_votes')}</span>
                    <span class="tooltip-stat-value">${i18n.fmtNum(party.votes)}</span>
                </div>
                ${info.ideology ? `
                <div class="tooltip-stat">
                    <span class="tooltip-stat-label">${i18n.t('ideology_label')}</span>
                    <span class="tooltip-stat-value">${info.ideology}</span>
                </div>
                ` : ''}
                ${info.founded ? `
                <div class="tooltip-stat">
                    <span class="tooltip-stat-label">${i18n.t('founded_label')}</span>
                    <span class="tooltip-stat-value">${info.founded}</span>
                </div>
                ` : ''}
                ${info.description ? `
                <div class="tooltip-description">${info.description}</div>
                ` : ''}
            </div>
        `;

        this.tooltip.innerHTML = html;
        this.tooltip.classList.add('visible');
        this.moveTooltip(event);
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

function init() {
    console.log('Initializing VoteTransferSankey...');
    try {
        window.sankey = new VoteTransferSankey('sankey-chart');
    } catch (error) {
        console.error('Failed to initialize:', error);
        document.getElementById('sankey-chart').innerHTML =
            `<div class="loading">${i18n.t('error_init')}: ${error.message}</div>`;
    }
}
