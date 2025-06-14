// chart.js
console.log('Starting chart.js');

import { showSidebar, closeSidebar } from './sidebar.js';

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

let currentZoom; // Store zoom behavior for external control

// Export zoom functions for external use
export function zoomIn() {
  console.log('External zoom in called');
  console.log('currentZoom available:', !!currentZoom);
  const svg = d3.select("#hierarchy-chart svg");
  console.log('SVG found:', !svg.empty());
  
  if (!svg.empty() && currentZoom) {
    console.log('Applying zoom in...');
    svg.transition().duration(300).call(
      currentZoom.scaleBy, 1.5
    );
  } else {
    console.log('No SVG or zoom behavior found - currentZoom:', currentZoom);
  }
}

export function zoomOut() {
  console.log('External zoom out called');
  console.log('currentZoom available:', !!currentZoom);
  const svg = d3.select("#hierarchy-chart svg");
  console.log('SVG found:', !svg.empty());
  
  if (!svg.empty() && currentZoom) {
    console.log('Applying zoom out...');
    svg.transition().duration(300).call(
      currentZoom.scaleBy, 1 / 1.5
    );
  } else {
    console.log('No SVG or zoom behavior found - currentZoom:', currentZoom);
  }
}

export function resetZoom() {
  console.log('External reset zoom called');
  console.log('currentZoom available:', !!currentZoom);
  const svg = d3.select("#hierarchy-chart svg");
  console.log('SVG found:', !svg.empty());
  
  if (!svg.empty() && currentZoom) {
    console.log('Applying zoom reset...');
    const container = document.getElementById('hierarchy-chart');
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    const initialTransform = d3.zoomIdentity
      .translate(width/2, 50)
      .scale(1);
    
    svg.transition().duration(500).call(
      currentZoom.transform, initialTransform
    );
  } else {
    console.log('No SVG or zoom behavior found - currentZoom:', currentZoom);
  }
}

export function initChart(data) {
  console.log('initChart called with data:', data);
  
  // Debounce resize handling
  const resizeObserver = new ResizeObserver(debounce(() => {
    updateChart(data);
    // Don't re-add zoom controls on resize to avoid conflicts
    // setTimeout(() => addZoomControls(), 50);
  }, 250));
  
  resizeObserver.observe(document.getElementById('hierarchy-chart'));
  
  // Initial chart render
  updateChart(data);
  
  // Don't add chart.js zoom controls - using test controls instead
  // setTimeout(() => {
  //   console.log('Adding zoom controls after chart render');
  //   addZoomControls();
  // }, 200);
  
  console.log('Chart initialization completed without adding duplicate zoom controls');
}

function addZoomControls() {
  const container = document.getElementById('hierarchy-chart');
  
  // Remove existing zoom controls if any
  const existingControls = container.querySelector('.zoom-controls');
  if (existingControls) {
    existingControls.remove();
  }
  
  // Create zoom controls container
  const zoomControls = document.createElement('div');
  zoomControls.className = 'zoom-controls';
  zoomControls.innerHTML = `
    <button id="zoom-in" class="zoom-btn zoom-in-btn" title="Zoom In">
      +
    </button>
    <button id="zoom-out" class="zoom-btn zoom-out-btn" title="Zoom Out">
      −
    </button>
    <button id="zoom-reset" class="zoom-btn zoom-reset-btn" title="Reset Zoom">
      ⌂
    </button>
  `;
  
  // Add to container
  container.appendChild(zoomControls);
  
  // Debug: log that controls were added
  console.log('Added zoom controls to container');
  console.log('Container children:', container.children.length);
  
  // Add event listeners
  document.getElementById('zoom-in').addEventListener('click', () => {
    console.log('Zoom in clicked');
    zoomIn();
  });
  document.getElementById('zoom-out').addEventListener('click', () => {
    console.log('Zoom out clicked');
    zoomOut();
  });
  document.getElementById('zoom-reset').addEventListener('click', () => {
    console.log('Zoom reset clicked');
    resetZoom();
  });
}

function updateChart(data) {
  console.log('updateChart called');
  
  // Get the container dimensions
  const container = document.getElementById('hierarchy-chart');
  const width = container.clientWidth;
  const height = container.clientHeight;

  console.log('Container dimensions:', width, 'x', height);

  // Clear existing SVG content (but preserve zoom controls)
  const svg = d3.select("#hierarchy-chart svg");
  if (!svg.empty()) {
    svg.remove();
    console.log('Removed existing SVG');
  }

  // Create SVG with defined viewBox for better scaling
  const newSvg = d3.select("#hierarchy-chart")
    .append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .attr("preserveAspectRatio", "xMidYMid meet");

  console.log('Created new SVG');

  // Create container for zoom
  const g = newSvg.append("g");

  // Add zoom behavior
  const zoom = d3.zoom()
    .scaleExtent([0.1, 3])
    .on("zoom", (event) => {
      g.attr("transform", event.transform);
    });

  // Store zoom for external control
  currentZoom = zoom;
  newSvg.call(zoom);

  console.log('Added zoom behavior, currentZoom set:', !!currentZoom);
  
  // Make currentZoom globally accessible for debugging
  window.currentZoom = currentZoom;
  console.log('currentZoom made globally accessible');

  // Pre-compute the hierarchy
  const root = d3.hierarchy(data[0]);
  const tree = d3.tree()
    .size([width - 100, height - 100])
    .separation((a, b) => (a.parent == b.parent ? 1 : 1.2));
  
  tree(root);

  // Create links
  const links = g.append("g")
    .attr("fill", "none")
    .attr("stroke", "#555")
    .attr("stroke-opacity", 0.4)
    .attr("stroke-width", 1.5)
    .selectAll("path")
    .data(root.links())
    .join("path")
    .attr("d", d3.linkVertical()
      .x(d => d.x)
      .y(d => d.y));

  // Create nodes group
  const nodeGroup = g.append("g")
    .attr("stroke-linejoin", "round")
    .attr("stroke-width", 3);

  // Batch node creation
  const nodes = nodeGroup.selectAll("g")
    .data(root.descendants())
    .join("g")
    .attr("transform", d => `translate(${d.x},${d.y})`);

  // Color scale
  const colorScale = d3.scaleOrdinal()
    .domain(["Group", "Company", "Team"])
    .range(["#1f77b4", "#ff7f0e", "#2ca02c"]);

  // Add circles to nodes
  nodes.append("circle")
    .attr("fill", d => d.parent ? (d.data.details === "Company" ? colorScale("Company") : colorScale("Team")) : colorScale("Top-level"))
    .attr("r", 6);

  // Add labels to nodes
  nodes.append("text")
    .attr("dy", "0.31em")
    .attr("x", d => d.children ? -12 : 12)
    .attr("text-anchor", d => d.children ? "end" : "start")
    .text(d => d.data.name)
    .style("font-size", "20px")
    .style("font-weight", "500")
    .style("font-family", "Arial, sans-serif")
    .clone(true).lower()
    .attr("stroke", "white")
    .attr("stroke-width", 4);

  // Add event listeners
  nodes.on("mouseover", function(event, d) {
    const usersList = d.data.users.map(user => `<li>${user.email}</li>`).join("");
    d3.select("#tooltip")
      .style("display", "block")
      .style("left", (event.pageX + 10) + "px")
      .style("top", (event.pageY - 10) + "px")
      .html(`
        <strong>Name:</strong> ${d.data.name}<br>
        <strong>Users:</strong> <ul>${usersList}</ul>
      `);
  })
  .on("mouseout", function() {
    d3.select("#tooltip").style("display", "none");
  })
  .on("click", function(event, d) {
    event.stopPropagation();
    showSidebar(d);
  });

  // Click handler for closing active displays when clicking outside
  d3.select("body").on("click", function(event) {
    if (event.target.closest('#details-sidebar') || 
        event.target.closest('.node') ||
        event.target.closest('.zoom-controls') ||
        event.target.closest('.test-zoom-controls')) {
      return;
    }
    closeSidebar();
  });
  
  // Center the initial view
  const initialTransform = d3.zoomIdentity
    .translate(width/2 - root.x, 50);
  newSvg.call(d3.zoom().transform, initialTransform);
  
  console.log('Chart rendering completed');
}

