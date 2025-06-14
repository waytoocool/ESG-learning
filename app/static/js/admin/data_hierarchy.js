console.log('Starting data_hierarchy.js');

import { initChart, zoomIn, zoomOut, resetZoom } from './chart.js';
import { showSidebar, closeSidebar } from './sidebar.js';
import { handleFormSubmit, handleUserFormSubmit } from './forms.js';

console.log('Imports completed, initChart function:', typeof initChart);
console.log('Zoom functions imported:', typeof zoomIn, typeof zoomOut, typeof resetZoom);

// Simple function to test adding zoom controls directly
function testAddZoomControls() {
  console.log('Testing direct zoom controls addition...');
  const container = document.getElementById('hierarchy-chart');
  
  if (!container) {
    console.error('Container not found for zoom controls test');
    return;
  }
  
  // Remove any existing test controls
  const existingTest = container.querySelector('.test-zoom-controls');
  if (existingTest) {
    existingTest.remove();
    console.log('Removed existing test controls');
  }
  
  // Clear any loading message
  const loadingMsg = container.querySelector('.loading');
  if (loadingMsg) {
    loadingMsg.remove();
    console.log('Removed loading message');
  }
  
  // Create a simple test div
  const testControls = document.createElement('div');
  testControls.className = 'test-zoom-controls';
  testControls.style.cssText = `
    position: absolute;
    top: 15px;
    right: 15px;
    z-index: 999;
    background: rgba(255, 255, 255, 0.95);
    border: 2px solid #2F4728;
    border-radius: 8px;
    padding: 8px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    transition: right 0.3s ease, z-index 0.3s ease;
  `;
  
  // Create buttons with IDs for event listeners
  const zoomInBtn = document.createElement('button');
  zoomInBtn.innerHTML = '+';
  zoomInBtn.id = 'test-zoom-in';
  zoomInBtn.style.cssText = 'width: 45px; height: 45px; border: 2px solid #2F4728; border-radius: 6px; background: #2F4728; color: white; cursor: pointer; font-size: 20px; font-weight: bold;';
  zoomInBtn.title = 'Zoom In';
  
  const zoomOutBtn = document.createElement('button');
  zoomOutBtn.innerHTML = '−';
  zoomOutBtn.id = 'test-zoom-out';
  zoomOutBtn.style.cssText = 'width: 45px; height: 45px; border: 2px solid #2F4728; border-radius: 6px; background: #2F4728; color: white; cursor: pointer; font-size: 20px; font-weight: bold;';
  zoomOutBtn.title = 'Zoom Out';
  
  const zoomResetBtn = document.createElement('button');
  zoomResetBtn.innerHTML = '⌂';
  zoomResetBtn.id = 'test-zoom-reset';
  zoomResetBtn.style.cssText = 'width: 45px; height: 45px; border: 2px solid #2F4728; border-radius: 6px; background: #2F4728; color: white; cursor: pointer; font-size: 20px; font-weight: bold;';
  zoomResetBtn.title = 'Reset Zoom';
  
  // Append buttons to container first
  testControls.appendChild(zoomInBtn);
  testControls.appendChild(zoomOutBtn);
  testControls.appendChild(zoomResetBtn);
  
  container.appendChild(testControls);
  
  // Add click event listeners using imported zoom functions AFTER appending to DOM
  zoomInBtn.addEventListener('click', (e) => {
    console.log('Test Zoom In clicked - calling imported function');
    e.preventDefault();
    e.stopPropagation();
    zoomIn();
  });
  
  zoomOutBtn.addEventListener('click', (e) => {
    console.log('Test Zoom Out clicked - calling imported function');
    e.preventDefault();
    e.stopPropagation();
    zoomOut();
  });
  
  zoomResetBtn.addEventListener('click', (e) => {
    console.log('Test Reset Zoom clicked - calling imported function');
    e.preventDefault();
    e.stopPropagation();
    resetZoom();
  });
  
  // Test if event listeners are working
  console.log('Added event listeners to buttons');
  
  // Add a test click listener to verify DOM events work
  testControls.addEventListener('click', (e) => {
    console.log('Click detected on test controls container:', e.target);
  });
  
  // Store reference for repositioning
  window.zoomControlsElement = testControls;
  
  console.log('Test zoom controls added successfully with imported zoom functions');
}

// Function to check if any drawers are open and adjust zoom controls
function adjustZoomControlsForDrawers() {
  const zoomControls = window.zoomControlsElement;
  if (!zoomControls) return;
  
  const entityDrawer = document.getElementById('entity-drawer');
  const userDrawer = document.getElementById('user-drawer');
  const detailsSidebar = document.getElementById('details-sidebar');
  
  // Check if any drawer is visible
  const isEntityDrawerOpen = entityDrawer && entityDrawer.style.display !== 'none';
  const isUserDrawerOpen = userDrawer && userDrawer.style.display !== 'none';
  const isDetailsSidebarOpen = detailsSidebar && detailsSidebar.classList.contains('open');
  
  const anyDrawerOpen = isEntityDrawerOpen || isUserDrawerOpen || isDetailsSidebarOpen;
  
  if (anyDrawerOpen) {
    // Move zoom controls to the left when drawer is open
    zoomControls.style.right = '320px'; // 300px drawer width + 20px margin
    zoomControls.style.zIndex = '998'; // Below drawer z-index
    console.log('Moved zoom controls to avoid drawer overlap');
  } else {
    // Reset position when no drawer is open
    zoomControls.style.right = '15px';
    zoomControls.style.zIndex = '999';
    console.log('Reset zoom controls to original position');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM Content Loaded');
  const chart = document.getElementById('hierarchy-chart');
  
  if (!chart) {
    console.error('Chart container not found!');
    return;
  }
  
  console.log('Chart container found:', chart);
  
  // Show loading state FIRST (this clears the container)
  chart.innerHTML = '<div class="loading">Loading chart...</div>';
  console.log('Loading state set, container cleared');
  
  // Check if data is available
  if (typeof data === 'undefined') {
    console.error('Data not available for chart');
    return;
  }
  
  console.log('Data available, initializing chart with data:', data);
  
  // Add test zoom controls AFTER the container is cleared
  setTimeout(() => {
    testAddZoomControls();
    // Check initial state of drawers and adjust zoom controls accordingly
    setTimeout(() => adjustZoomControlsForDrawers(), 100);
  }, 50);
  
  // Initialize chart with a small delay to ensure everything is ready
  setTimeout(() => {
    try {
      console.log('About to call initChart...');
      initChart(data);
      console.log('Chart initialization completed');
      
      // Show chart when ready
      chart.classList.add('loaded');
    } catch (error) {
      console.error('Error initializing chart:', error);
    }
  }, 200);

  // Set up event listeners

  const entityForm = document.getElementById('entity-form');
  if (entityForm) {
      entityForm.addEventListener('submit', (event) => {
          handleFormSubmit(event);
      });
  }

  const userForm = document.getElementById('user-form');
  if (userForm) {
      userForm.addEventListener('submit', (event) => {
          handleUserFormSubmit(event);
      });
  }  
  
  document.getElementById("open-entity-drawer").addEventListener("click", () => {
    document.getElementById("entity-drawer").style.display = "block";
    setTimeout(() => adjustZoomControlsForDrawers(), 50); // Small delay for DOM update
  });

  document.getElementById("open-user-drawer").addEventListener("click", () => {
    document.getElementById("user-drawer").style.display = "block";
    setTimeout(() => adjustZoomControlsForDrawers(), 50); // Small delay for DOM update
  });

  document.getElementById("close-drawer").addEventListener("click", () => {
    document.getElementById("entity-drawer").style.display = "none";
    setTimeout(() => adjustZoomControlsForDrawers(), 50); // Small delay for DOM update
  });

  document.getElementById("close-user-drawer").addEventListener("click", () => {
    document.getElementById("user-drawer").style.display = "none";
    setTimeout(() => adjustZoomControlsForDrawers(), 50); // Small delay for DOM update
  });
  
  // Also monitor the details sidebar if it gets opened via chart interactions
  const detailsSidebar = document.getElementById("details-sidebar");
  if (detailsSidebar) {
    // Use MutationObserver to watch for class changes on the sidebar
    const observer = new MutationObserver(() => {
      setTimeout(() => adjustZoomControlsForDrawers(), 50);
    });
    
    observer.observe(detailsSidebar, {
      attributes: true,
      attributeFilter: ['class']
    });
  }
});


