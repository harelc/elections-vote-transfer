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
            toggleValue.textContent = isSource ? 'מהבחירות הקודמות' : 'מהבחירות החדשות';
        }

        // Update mobile toggle
        const mobileToggleValue = document.getElementById('mobile-toggle-value');
        if (mobileToggleValue) {
            mobileToggleValue.textContent = isSource ? '% מהקודמות' : '% מהחדשות';
        }
    }

    showBottomSheet(link) {
        if (!this.bottomSheet || !this.bottomSheetContent) return;

        const reversePercent = link.target.votes > 0
            ? ((link.value / link.target.votes) * 100).toFixed(1)
            : 0;

        const isSource = this.percentMode === 'source';
        const percent = isSource ? link.percentage : reversePercent;
        const description = isSource
            ? `מקולות ${link.sourceName} בבחירות הקודמות`
            : `מקולות ${link.targetName} בבחירות החדשות`;

        this.bottomSheetContent.innerHTML = `
            <div class="sheet-parties">
                <span class="sheet-party">
                    <span class="sheet-party-color" style="background: ${link.source.color}"></span>
                    ${link.sourceName}
                </span>
                <span class="sheet-arrow">←</span>
                <span class="sheet-party">
                    <span class="sheet-party-color" style="background: ${link.target.color}"></span>
                    ${link.targetName}
                </span>
            </div>
            <div class="sheet-percent">${percent}%</div>
            <div class="sheet-description">${description}</div>
            <div class="sheet-votes">${link.value.toLocaleString('he-IL')} קולות (מתוך הקלפיות המשותפות)</div>
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
        const electionType = node.side === 'from' ? 'בבחירות הקודמות' : 'בבחירות החדשות';

        this.bottomSheetContent.innerHTML = `
            <div class="sheet-party-details">
                <div class="sheet-party-header">
                    <span class="sheet-party-color" style="background: ${node.color}"></span>
                    <span class="sheet-party-name">${node.name}</span>
                </div>
                <div class="sheet-party-votes">${node.votes.toLocaleString('he-IL')} קולות ${electionType}</div>
                ${node.seats ? `<div class="sheet-party-seats">${node.seats} מנדטים</div>` : ''}
                ${info.leader ? `
                    <div class="sheet-party-leader">
                        ${info.leader_image ? `<img class="sheet-leader-img" src="${info.leader_image}" alt="${info.leader}" onerror="this.style.display='none'">` : ''}
                        <div class="sheet-leader-info">
                            <span class="sheet-leader-label">מנהיג:</span>
                            <span class="sheet-leader-name">${info.leader}</span>
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

        if (fromTitle) fromTitle.textContent = this.data.from_election.name;
        if (toTitle) toTitle.textContent = this.data.to_election.name;

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
                    <span class="legend-row-name">${party.name}</span>
                    <span class="legend-row-votes">${party.votes.toLocaleString('he-IL')}</span>
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
        this.container.innerHTML = '<div class="loading">טוען נתונים...</div>';

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
            this.container.innerHTML = `<div class="loading">שגיאה בטעינת הנתונים: ${error.message}</div>`;
        }
    }

    updateInfo() {
        const { from_election, to_election, stats } = this.data;

        // Update election info
        document.getElementById('from-election-name').textContent = from_election.name;
        document.getElementById('from-election-date').textContent = this.formatDate(from_election.date);
        document.getElementById('to-election-name').textContent = to_election.name;
        document.getElementById('to-election-date').textContent = this.formatDate(to_election.date);

        // Update voter statistics for "from" election
        if (from_election.eligible_voters) {
            document.getElementById('from-eligible').textContent = from_election.eligible_voters.toLocaleString('he-IL');
            document.getElementById('from-votes').textContent = from_election.votes_cast.toLocaleString('he-IL');
            document.getElementById('from-turnout').textContent = from_election.turnout_percent.toFixed(1) + '%';
        }

        // Update voter statistics for "to" election
        if (to_election.eligible_voters) {
            document.getElementById('to-eligible').textContent = to_election.eligible_voters.toLocaleString('he-IL');
            document.getElementById('to-votes').textContent = to_election.votes_cast.toLocaleString('he-IL');
            document.getElementById('to-turnout').textContent = to_election.turnout_percent.toFixed(1) + '%';
        }

        // Update stats
        document.getElementById('stat-precincts').textContent = stats.common_precincts.toLocaleString('he-IL');
        document.getElementById('stat-r2').textContent = stats.r_squared.toFixed(3);
    }

    formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('he-IL', { day: '2-digit', month: '2-digit', year: 'numeric' });
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
            this.container.innerHTML = '<div class="loading">אין נתונים להצגה</div>';
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
            .text(d => d.name)
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

        let html = `
            <div class="tooltip-header">
                <div class="tooltip-color" style="background-color: ${node.color}"></div>
                <span class="tooltip-title">${node.name}</span>
                <span class="tooltip-symbol">(${node.symbol})</span>
            </div>
            <div class="tooltip-body">
                <div class="tooltip-stat">
                    <span class="tooltip-stat-label">סה״כ קולות:</span>
                    <span class="tooltip-stat-value">${node.votes.toLocaleString('he-IL')}</span>
                </div>
                ${info.leader ? `
                <div class="tooltip-stat">
                    <span class="tooltip-stat-label">מנהיג:</span>
                    <span class="tooltip-stat-value">${info.leader}</span>
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

        const percentText = this.percentMode === 'source'
            ? `${link.percentage}% מקולות ${link.sourceName} בבחירות הקודמות`
            : `${reversePercent}% מקולות ${link.targetName} בבחירות החדשות`;

        const html = `
            <div class="tooltip-flow">
                <div class="tooltip-flow-parties">
                    <span class="tooltip-flow-party">${link.sourceName}</span>
                    <span class="tooltip-flow-arrow">←</span>
                    <span class="tooltip-flow-party">${link.targetName}</span>
                </div>
                <div class="tooltip-flow-value">${percentText}</div>
                <div class="tooltip-flow-note">${link.value.toLocaleString('he-IL')} קולות (מתוך הקלפיות המשותפות בלבד)</div>
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
            title.textContent = `תוצאות רשמיות - כנסת ה-${electionName.replace('הכנסת ה-', '')}`;
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
                ? `<span class="legend-seats">${party.seats} מנדטים</span>`
                : `<span class="legend-seats below">לא עברה</span>`;

            item.innerHTML = `
                <div class="legend-color" style="background-color: ${color}"></div>
                <span class="legend-name">${party.name}</span>
                <span class="legend-votes">${party.votes.toLocaleString('he-IL')} קולות</span>
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

        let html = `
            <div class="tooltip-party">
                <div class="tooltip-party-header">
                    ${info.logo ? `<img class="tooltip-logo" src="${info.logo}" alt="${party.name}" onerror="this.style.display='none'">` : ''}
                    <div class="tooltip-party-title">
                        <span class="tooltip-party-name">${party.name}</span>
                        ${info.name_en ? `<span class="tooltip-party-name-en">${info.name_en}</span>` : ''}
                    </div>
                </div>
                ${info.leader_image ? `
                <div class="tooltip-leader">
                    <img class="tooltip-leader-image" src="${info.leader_image}" alt="${info.leader}" onerror="this.style.display='none'">
                    <div class="tooltip-leader-info">
                        <span class="tooltip-leader-label">מנהיג:</span>
                        <span class="tooltip-leader-name">${info.leader || ''}</span>
                    </div>
                </div>
                ` : (info.leader ? `
                <div class="tooltip-stat">
                    <span class="tooltip-stat-label">מנהיג:</span>
                    <span class="tooltip-stat-value">${info.leader}</span>
                </div>
                ` : '')}
                <div class="tooltip-stat">
                    <span class="tooltip-stat-label">סה״כ קולות:</span>
                    <span class="tooltip-stat-value">${party.votes.toLocaleString('he-IL')}</span>
                </div>
                ${info.ideology ? `
                <div class="tooltip-stat">
                    <span class="tooltip-stat-label">אידאולוגיה:</span>
                    <span class="tooltip-stat-value">${info.ideology}</span>
                </div>
                ` : ''}
                ${info.founded ? `
                <div class="tooltip-stat">
                    <span class="tooltip-stat-label">שנת הקמה:</span>
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
            `<div class="loading">שגיאה באתחול: ${error.message}</div>`;
    }
}
