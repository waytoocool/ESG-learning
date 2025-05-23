console.log('Starting data_hierarchy.js');

import { initChart } from './chart.js';
import { showSidebar, closeSidebar } from './sidebar.js';
import { handleFormSubmit, handleUserFormSubmit } from './forms.js';

document.addEventListener('DOMContentLoaded', () => {
  const chart = document.getElementById('hierarchy-chart');
  
  // Show loading state
  chart.innerHTML = '<div class="loading">Loading chart...</div>';
  
  // Initialize chart
  initChart(data);
  
  // Show chart when ready
  chart.classList.add('loaded');

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
  });

  document.getElementById("open-user-drawer").addEventListener("click", () => {
    document.getElementById("user-drawer").style.display = "block";
  });

  document.getElementById("close-drawer").addEventListener("click", () => {
    document.getElementById("entity-drawer").style.display = "none";
  });

  document.getElementById("close-user-drawer").addEventListener("click", () => {
    document.getElementById("user-drawer").style.display = "none";
  });

});


