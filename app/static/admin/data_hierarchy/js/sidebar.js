console.log('Starting sidebar.js');

export function showSidebar(d) {
    const sidebar = d3.select("#details-sidebar");
    const content = generateEntityDetails(d);

    document.getElementById("sidebar-title").textContent = d.data.name;
    sidebar.select(".details-sidebar-content").html(content);
    sidebar.classed("open", true);
}

export function closeSidebar() {
    d3.select("#details-sidebar").classed("open", false);
}  

function showTooltip(event, d) {
    // Simplified tooltip content with just users count
    const tooltipContent = generateEntityDetailsMini(d);

    d3.select("#tooltip")
        .style("display", "block")
        .style("left", (event.pageX + 10) + "px")
        .style("top", (event.pageY - 10) + "px")
        .select(".tooltip-content")
        .html(tooltipContent);
}

function hideTooltip() {
    d3.select("#tooltip").style("display", "none");
}

// function are responsible for generating the HTML content for the entity details for sidebar
function generateEntityDetails(d) {
    const usersList = d.data.users.map(user => {
        // Check if there's an active cooldown for this user
        const cooldownKey = `resend_cooldown_${user.email}`;
        const hasCooldown = localStorage.getItem(cooldownKey);

        return `
            <div class="user-item">
                <div class="user-header">
                    <span class="user-name">${user.name} (${user.username})</span>
                    ${user.is_email_verified ? 
                        `<span class="verified-user">✓ Verified
                            <span class="info-icon" title="Email verified on ${user.verification_date}">i</span>
                        </span>` : 
                        `<span class="unverified-user">✗ Unverified
                            ${!hasCooldown ? 
                                `<button class="resend-verification-btn" 
                                    onclick="handleVerificationResend('${user.email}')"
                                    title="Click to resend verification email">
                                    Resend Verification
                                </button>` :
                                `<span class="cooldown-message">Verification email sent</span>`
                            }
                        </span>`
                    }
                </div>
                <div class="user-email">${user.email}</div>
            </div>
        `;
    }).join("");

    return `
        <div class="entity-details">
            <div class="entity-header">
                <h4>${d.data.name}</h4>
                <span class="entity-type">${d.data.details}</span>
            </div>
            <div class="users-section">
                <h5>Users (${d.data.users.length})</h5>
                <div class="user-list">
                    ${usersList}
                </div>
            </div>
        </div>
    `;
}

// function are responsible for generating the HTML content for the entity details for tooltip/ hover
function generateEntityDetailsMini(d) {
    const usersList = d.data.users.map(user => {

        return `
            <div class="user-item">
                <div class="user-header">
                    <span class="user-name">${user.name} (${user.username})</span>
                    ${user.is_email_verified ? 
                        `<span class="verified-user">✓ Verified
                            <span class="info-icon" title="Email verified on ${user.verification_date}">i</span>
                        </span>` : 
                        `<span class="unverified-user">✗ Unverified
                            ${!hasCooldown ? 
                                `<button class="resend-verification-btn" 
                                    onclick="handleVerificationResend('${user.email}')"
                                    title="Click to resend verification email">
                                    Resend Verification
                                </button>` :
                                `<span class="cooldown-message">Verification email sent</span>`
                            }
                        </span>`
                    }
                </div>
                <div class="user-email">${user.email}</div>
            </div>
        `;
    }).join("");

    return `
        <div class="entity-details">
            <div class="entity-header">
                <h4>${d.data.name}</h4>
                <span class="entity-type">${d.data.details}</span>
            </div>
            <div class="users-section">
                <h5>Users (${d.data.users.length})</h5>
            </div>
        </div>
    `;
}