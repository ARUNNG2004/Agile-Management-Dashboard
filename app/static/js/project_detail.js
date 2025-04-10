document.addEventListener('DOMContentLoaded', function() {
    // Get project ID from URL
    const projectId = window.location.pathname.split('/').pop();

    // Fetch project details
    fetchProjectDetails(projectId);

    // Set up event listeners
    setupEventListeners(projectId);

    // Check if user is product owner or scrum master to show edit buttons
    checkUserRole();
});

// Fetch project details from the API
function fetchProjectDetails(projectId) {
    fetch(`/api/project/${projectId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch project details');
            }
            return response.json();
        })
        .then(data => {
            populateProjectDetails(data);
            fetchSprints(projectId);
            fetchUserStories(projectId);
            fetchTeamPerformance(projectId);
        })
        .catch(error => {
            console.error('Error fetching project details:', error);
            displayError('Failed to load project details. Please try again later.');
        });
}

// Display project details on the page
function populateProjectDetails(project) {
    // Populate project header and information
    document.getElementById('projectName').textContent = project.project_name;
    document.getElementById('projectDescription').textContent = project.project_description;

    // Populate project information table
    document.getElementById('projectId').textContent = project.project_id;
    document.getElementById('productOwner').textContent = project.product_owner;
    document.getElementById('startDate').textContent = project.start_date;
    document.getElementById('endDate').textContent = project.end_date;
    document.getElementById('revisedEndDate').textContent = project.revised_end_date || 'N/A';

    // Set project status with appropriate badge
    const statusBadge = getStatusBadge(project.status);
    document.getElementById('projectStatus').innerHTML = statusBadge;

    // Populate team members
    populateTeamMembers(project.scrum_masters, 'scrumMastersList');
    populateTeamMembers(project.development_team, 'devTeamList');

    // Initialize the edit form with current values
    document.getElementById('editProjectId').value = project.id;
    document.getElementById('editProjectName').value = project.project_name;
    document.getElementById('editProjectDescription').value = project.project_description;
    document.getElementById('editStartDate').value = project.start_date;
    document.getElementById('editEndDate').value = project.end_date;
    document.getElementById('editRevisedEndDate').value = project.revised_end_date || '';
    // document.getElementById('editStatus').value = project.status;
}

// Helper function to get status badge HTML
function getStatusBadge(status) {
    const statusClass = {
        'Not Started': 'badge-secondary',
        'Ongoing': 'badge-primary',
        'Completed': 'badge-success',
        'Delayed': 'badge-warning'
    };

    return `<span class="badge ${statusClass[status] || 'badge-secondary'}">${status}</span>`;
}

// Populate team members list
function populateTeamMembers(members, elementId) {
    const listElement = document.getElementById(elementId);
    listElement.innerHTML = '';

    if (!members || members.length === 0) {
        listElement.innerHTML = '<li class="list-group-item">No members assigned</li>';
        return;
    }

    members.forEach(member => {
        const li = document.createElement('li');
        li.className = 'list-group-item';
        li.textContent = member;
        listElement.appendChild(li);
    });
}

// Fetch sprints for the project
function fetchSprints(projectId) {
    fetch(`/api/project/${projectId}/sprints`)
        .then(response => response.json())
        .then(data => {
            populateSprintsTable(data);
            updateSprintDropdowns(data);
        })
        .catch(error => {
            console.error('Error fetching sprints:', error);
        });
}

// Populate sprints table
function populateSprintsTable(sprints) {
    const sprintTableBody = document.querySelector('#sprintTable tbody');
    sprintTableBody.innerHTML = '';

    if (!sprints || sprints.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="6" class="text-center">No sprints available for this project</td>';
        sprintTableBody.appendChild(row);
        return;
    }

    sprints.forEach(sprint => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${sprint.sprint_number}</td>
            <td>${sprint.scrum_master}</td>
            <td>${sprint.start_date}</td>
            <td>${sprint.end_date}</td>
            <td>${getSprintStatusBadge(sprint.status)}</td>
            <td>
                <button class="btn btn-sm btn-info view-stories" data-sprint-id="${sprint.id}">
                    <i class="fas fa-list"></i> View Stories
                </button>
                <button class="btn btn-sm btn-warning edit-sprint" data-sprint-id="${sprint.id}">
                    <i class="fas fa-edit"></i> Edit
                </button>
            </td>
        `;
        sprintTableBody.appendChild(row);

        // Add event listener for viewing stories
        row.querySelector('.view-stories').addEventListener('click', () => {
            showSprintStories(sprint.stories);
        });
    });
}

function showSprintStories(stories) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Sprint User Stories</h5>
                    <button type="button" class="close" data-dismiss="modal">&times;</button>
                </div>
                <div class="modal-body">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Description</th>
                                <th>Team</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${stories.map(story => `
                                <tr>
                                    <td>${story.id}</td>
                                    <td>${story.description}</td>
                                    <td>${story.team}</td>
                                    <td>${getUserStoryStatusBadge(story.status)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    $(modal).modal('show');
    $(modal).on('hidden.bs.modal', function () {
        modal.remove();
    });
}

// Helper function to get sprint status badge
function getSprintStatusBadge(status) {
    const statusClasses = {
        'Not Started': 'badge-secondary',
        'In Progress': 'badge-primary',
        'Completed': 'badge-success'
    };
    return `<span class="badge ${statusClasses[status] || 'badge-secondary'}">${status}</span>`;
}

// Fetch user stories for the project
function fetchUserStories(projectId) {
    fetch(`/api/project/${projectId}/user-stories`)
        .then(response => response.json())
        .then(data => {
            populateUserStoriesTable(data);
            updateCompletionMetrics(data);
        })
        .catch(error => {
            console.error('Error fetching user stories:', error);
        });
}

// Populate user stories table
function populateUserStoriesTable(stories) {
    const storiesTableBody = document.querySelector('#userStoryTable tbody');
    storiesTableBody.innerHTML = '';

    if (!stories || stories.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="8" class="text-center">No user stories available for this project</td>';
        storiesTableBody.appendChild(row);
        return;
    }

    stories.forEach(story => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${story.id}</td>
            <td>${story.description}</td>
            <td>${story.planned_sprint}</td>
            <td>${story.actual_sprint || 'N/A'}</td>
            <td>${story.story_point}</td>
            <td>${story.assignee}</td>

            <td>${getUserStoryStatusBadge(story.status)}</td>
            <td>
                <button class="btn btn-sm btn-warning edit-story" data-id="${story.id}">
                    <i class="fas fa-edit"></i> Edit
                </button>
            </td>
        `;
        storiesTableBody.appendChild(row);
    });
}

// Helper function to get user story status badge
function getUserStoryStatusBadge(status) {
    const statusClasses = {
        'Not Started': 'badge-secondary',
        'Assigned': 'badge-info',
        'In Progress': 'badge-primary',
        'Completed': 'badge-success'
    };
    return `<span class="badge ${statusClasses[status] || 'badge-secondary'}">${status}</span>`;
}

// Update completion metrics
function updateCompletionMetrics(stories) {
    if (!stories || stories.length === 0) {
        return;
    }

    const totalStories = stories.length;
    const completedStories = stories.filter(story => story.status === 'Completed').length;
    const completionPercentage = Math.round((completedStories / totalStories) * 100);

    // Update progress bar
    const progressBar = document.getElementById('completionProgressBar');
    progressBar.style.width = `${completionPercentage}%`;
    progressBar.setAttribute('aria-valuenow', completionPercentage);
    progressBar.textContent = `${completionPercentage}%`;

    // Update completion circle
    document.getElementById('completion-percentage').textContent = `${completionPercentage}%`;
    updateCompletionCircle(completionPercentage);

    // Update story count text
    document.getElementById('completedStories').textContent = completedStories;
    document.getElementById('totalStories').textContent = totalStories;
}

// Update the completion circle visualization
function updateCompletionCircle(percentage) {
    const circle = document.getElementById('completion-circle');
    circle.style.background = `conic-gradient(
        #28a745 0% ${percentage}%,
        #e9ecef ${percentage}% 100%
    )`;
}

// Fetch team performance data
function fetchTeamPerformance(projectId) {
    Promise.all([
        fetch(`/api/project/${projectId}/velocity-chart`).then(response => response.json()),
        fetch(`/api/project/${projectId}/sprint-progress`).then(response => response.json()),
        fetch(`/api/project/${projectId}/individual-performance`).then(response => response.json())
    ])
    .then(([velocityData, sprintProgressData, individualPerformanceData]) => {
        renderVelocityChart(velocityData);
        renderSprintProgressChart(sprintProgressData);
        renderIndividualPerformanceTable(individualPerformanceData);
    })
    .catch(error => {
        console.error('Error fetching performance data:', error);
    });
}

// Render velocity chart
function renderVelocityChart(data) {
    const ctx = document.getElementById('velocityChart').getContext('2d');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Team Velocity',
                data: data.velocity,
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 2,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Story Points'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Sprint'
                    }
                }
            }
        }
    });
}

// Render sprint progress chart
function renderSprintProgressChart(data) {
    const ctx = document.getElementById('sprintProgressChart').getContext('2d');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Completed',
                    data: data.completed,
                    backgroundColor: 'rgba(40, 167, 69, 0.7)'
                },
                {
                    label: 'In Progress',
                    data: data.in_progress,
                    backgroundColor: 'rgba(23, 162, 184, 0.7)'
                },
                {
                    label: 'Not Started',
                    data: data.not_started,
                    backgroundColor: 'rgba(108, 117, 125, 0.7)'
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    stacked: true,
                    title: {
                        display: true,
                        text: 'Sprint'
                    }
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Stories'
                    }
                }
            }
        }
    });
}

// Render individual performance table
function renderIndividualPerformanceTable(data) {
    const tableBody = document.querySelector('#individualPerformanceTable tbody');
    tableBody.innerHTML = '';

    if (!data || data.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="5" class="text-center">No individual performance data available</td>';
        tableBody.appendChild(row);
        return;
    }

    data.forEach(member => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${member.name}</td>
            <td>${member.assigned_stories}</td>
            <td>${member.completed_stories}</td>
            <td>${member.story_points}</td>
            <td>
                <div class="progress">
                    <div class="progress-bar bg-${getPerformanceClass(member.performance_score)}"
                         role="progressbar"
                         style="width: ${member.performance_score}%;"
                         aria-valuenow="${member.performance_score}"
                         aria-valuemin="0"
                         aria-valuemax="100">
                        ${member.performance_score}%
                    </div>
                </div>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

// Helper function to get performance class based on score
function getPerformanceClass(score) {
    if (score >= 80) return 'success';
    if (score >= 60) return 'info';
    if (score >= 40) return 'warning';
    return 'danger';
}

// Update sprint dropdowns in user story edit form
function updateSprintDropdowns(sprints) {
    const plannedSprintDropdown = document.getElementById('editPlannedSprint');
    const actualSprintDropdown = document.getElementById('editActualSprint');

    // Clear existing options
    plannedSprintDropdown.innerHTML = '';
    actualSprintDropdown.innerHTML = '';

    // Add "None" option for actual sprint
    const noneOption = document.createElement('option');
    noneOption.value = '';
    noneOption.textContent = 'None';
    actualSprintDropdown.appendChild(noneOption);

    // Add options for each sprint
    sprints.forEach(sprint => {
        const plannedOption = document.createElement('option');
        plannedOption.value = sprint.sprint_no;
        plannedOption.textContent = `Sprint ${sprint.sprint_no}`;
        plannedSprintDropdown.appendChild(plannedOption.cloneNode(true));

        const actualOption = document.createElement('option');
        actualOption.value = sprint.sprint_no;
        actualOption.textContent = `Sprint ${sprint.sprint_no}`;
        actualSprintDropdown.appendChild(actualOption);
    });
}

// Set up event listeners
function setupEventListeners(projectId) {
    // Save project changes
    document.getElementById('saveProjectChanges').addEventListener('click', function() {
        const formData = new FormData(document.getElementById('editProjectForm'));

        fetch(`/api/project/${projectId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(Object.fromEntries(formData))
        })
        .then(response => response.json())
        .then(data => {
            $('#editProjectModal').modal('hide');
            if (data.success) {
                showSuccessAlert('Project updated successfully');
                fetchProjectDetails(projectId);
            } else {
                showErrorAlert(data.message || 'Failed to update project');
            }
        })
        .catch(error => {
            console.error('Error updating project:', error);
            showErrorAlert('An error occurred while updating the project');
        });
    });

    // Save user story changes
    document.getElementById('saveUserStoryChanges').addEventListener('click', function() {
        const formData = new FormData(document.getElementById('editUserStoryForm'));
        const storyId = document.getElementById('editUserStoryId').value;

        fetch(`/api/user-story/${storyId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(Object.fromEntries(formData))
        })
        .then(response => response.json())
        .then(data => {
            $('#editUserStoryModal').modal('hide');
            if (data.success) {
                showSuccessAlert('User story updated successfully');
                fetchUserStories(projectId);
            } else {
                showErrorAlert(data.message || 'Failed to update user story');
            }
        })
        .catch(error => {
            console.error('Error updating user story:', error);
            showErrorAlert('An error occurred while updating the user story');
        });
    });

    // Edit project button
    document.addEventListener('click', function(e) {
        if (e.target.closest('.edit-project')) {
            $('#editProjectModal').modal('show');
        }
    });

    // Edit user story button
    document.addEventListener('click', function(e) {
        const editButton = e.target.closest('.edit-story');
        if (editButton) {
            const storyId = editButton.dataset.id;

            fetch(`/api/user-story/${storyId}`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('editUserStoryId').value = data.id;
                    document.getElementById('editStoryDescription').value = data.description;
                    document.getElementById('editPlannedSprint').value = data.planned_sprint;
                    document.getElementById('editActualSprint').value = data.actual_sprint || '';
                    document.getElementById('editStoryPoints').value = data.story_point;
                    // document.getElementById('editStoryStatus').value = data.status;

                    // Populate assignee dropdown
                    const assigneeDropdown = document.getElementById('editAssignee');
                    assigneeDropdown.innerHTML = '';

                    fetch(`/api/project/${projectId}/team-members`)
                        .then(response => response.json())
                        .then(members => {
                            members.forEach(member => {
                                const option = document.createElement('option');
                                option.value = member;
                                option.textContent = member;
                                option.selected = member === data.assignee;
                                assigneeDropdown.appendChild(option);
                            });

                            $('#editUserStoryModal').modal('show');
                        });
                })
                .catch(error => {
                    console.error('Error fetching user story details:', error);
                    showErrorAlert('Failed to load user story details');
                });
        }
    });

    // Add status change handler
    const statusSelect = document.getElementById('projectStatus');
    if (statusSelect) {
        statusSelect.addEventListener('change', function() {
            updateProjectStatus(projectId, this.value);
        });
    }
}

// Check if user is product owner or scrum master
function checkUserRole() {
    fetch('/api/check-user-role')
        .then(response => response.json())
        .then(data => {
            if (data.can_edit) {
                // Show edit buttons
                document.getElementById('editProjectBtns').innerHTML = `
                    <button class="btn btn-warning edit-project">
                        <i class="fas fa-edit"></i> Edit Project
                    </button>
                `;

                document.getElementById('sprintActionBtns').innerHTML = `
                    <button class="btn btn-sm btn-success" id="addSprintBtn">
                        <i class="fas fa-plus"></i> Add Sprint
                    </button>
                `;

                document.getElementById('userStoryActionBtns').innerHTML = `
                    <button class="btn btn-sm btn-success" id="addUserStoryBtn">
                        <i class="fas fa-plus"></i> Add User Story
                    </button>
                `;
            }
        })
        .catch(error => {
            console.error('Error checking user role:', error);
        });
}

// Display error message
function displayError(message) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
            <span aria-hidden="true">&times;</span>
        </button>
    `;

    // Insert at top of container
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 150);
    }, 3000);
}

// Show success alert
function showSuccessAlert(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show';
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
            <span aria-hidden="true">&times;</span>
        </button>
    `;

    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);

    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 150);
    }, 3000);
}

// Show error alert
function showErrorAlert(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
            <span aria-hidden="true">&times;</span>
        </button>
    `;

    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);

    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 150);
    }, 5000);
}

// Add this function to handle status updates
function updateProjectStatus(projectId, newStatus) {
    // First fetch current project details
    fetch(`/api/project/${projectId}`)
        .then(response => response.json())
        .then(project => {
            // Calculate status based on completion
            let calculatedStatus = determineProjectStatus(project);

            // Use calculated status if available, otherwise use selected status
            const finalStatus = calculatedStatus || newStatus;

            // Update status via API
            return fetch(`/api/project/${projectId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    status: finalStatus,
                    auto_calculated: calculatedStatus !== null
                })
            });
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update UI
                const statusBadge = document.getElementById('projectStatus');
                statusBadge.innerHTML = getStatusBadge(newStatus);
                showSuccessAlert('Project status updated successfully');

                // Refresh project details
                fetchProjectDetails(projectId);
            } else {
                showErrorAlert(data.message || 'Failed to update project status');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showErrorAlert('An error occurred while updating project status');
        });
}

function determineProjectStatus(project) {
    // Get all sprints and stories
    const sprints = project.sprints || [];
    const stories = project.user_stories || [];

    // Count completed items
    const totalSprints = sprints.length;
    const completedSprints = sprints.filter(sprint => sprint.status === 'Completed').length;
    const totalStories = stories.length;
    const completedStories = stories.filter(story => story.status === 'completed').length;

    // Calculate completion percentages
    const sprintCompletion = totalSprints > 0 ? (completedSprints / totalSprints) * 100 : 0;
    const storyCompletion = totalStories > 0 ? (completedStories / totalStories) * 100 : 0;

    // Determine status based on completion and dates
    const today = new Date();
    const startDate = new Date(project.start_date);
    const endDate = new Date(project.end_date);

    if (sprintCompletion === 100 && storyCompletion === 100) {
        return 'Completed';
    } else if (today < startDate) {
        return 'Not Started';
    } else if (today >= startDate && today <= endDate) {
        return 'Ongoing';
    } else if (today > endDate && (sprintCompletion < 100 || storyCompletion < 100)) {
        return 'Delayed';
    }

    return null; // Return null if no automatic status can be determined
}

