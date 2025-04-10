
document.addEventListener('DOMContentLoaded', function() {
    // Set today's date as the default for start date
    document.getElementById('startDate').valueAsDate = new Date();

    // Form containers
    const projectDetailsContainer = document.getElementById('projectDetailsContainer');
    const sprintSetupContainer = document.getElementById('sprintSetupContainer');
    const userStoriesContainer = document.getElementById('userStoriesContainer');

    // Navigation buttons
    const nextBtn = document.getElementById('nextBtn');
    const backToProjectBtn = document.getElementById('backToProjectBtn');
    const nextToStoriesBtn = document.getElementById('nextToStoriesBtn');
    const backToSprintsBtn = document.getElementById('backToSprintsBtn');
    const cancelBtn = document.getElementById('cancelBtn');

    // Generation buttons
    const generateSprintsBtn = document.getElementById('generateSprintsBtn');
    const generateStoriesBtn = document.getElementById('generateStoriesBtn');

    // Date validation
    document.getElementById('endDate').addEventListener('change', function() {
        const startDate = new Date(document.getElementById('startDate').value);
        const endDate = new Date(this.value);

        if (endDate < startDate) {
            alert('End date cannot be earlier than start date');
            this.value = '';
        }
    });

    document.getElementById('revisedEndDate').addEventListener('change', function() {
        const endDate = new Date(document.getElementById('endDate').value);
        const revisedDate = new Date(this.value);

        if (revisedDate < endDate) {
            alert('Revised end date should be later than the original end date');
            this.value = '';
        }
    });

    // Navigation handlers
    nextBtn.addEventListener('click', () => {
        if (validateProjectDetails()) {
            projectDetailsContainer.style.display = 'none';
            sprintSetupContainer.style.display = 'block';
        }
    });

    backToProjectBtn.addEventListener('click', () => {
        sprintSetupContainer.style.display = 'none';
        projectDetailsContainer.style.display = 'block';
    });

    nextToStoriesBtn.addEventListener('click', () => {
        if (validateSprints()) {
            sprintSetupContainer.style.display = 'none';
            userStoriesContainer.style.display = 'block';
        }
    });

    backToSprintsBtn.addEventListener('click', () => {
        userStoriesContainer.style.display = 'none';
        sprintSetupContainer.style.display = 'block';
    });

    cancelBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to cancel? All progress will be lost.')) {
            window.location.href = '/dashboard';
        }
    });

    // Sprint generation
    generateSprintsBtn.addEventListener('click', () => {
        const count = parseInt(document.getElementById('sprintCount').value);
        generateSprintForms(count);
    });

    // Story generation
    generateStoriesBtn.addEventListener('click', () => {
        const count = parseInt(document.getElementById('storyCount').value);
        generateStoryForms(count);
    });

    // Form submission
    document.getElementById('projectForm').addEventListener('submit', submitProject);

    // Add status change handler
    const statusSelect = document.getElementById('status');
    if (statusSelect) {
        statusSelect.addEventListener('change', function() {
            updateProjectStatus(this.value);
        });
    }

    function updateProjectStatus(status) {
        // Update any UI elements that depend on status
        const statusBadge = document.getElementById('statusBadge');
        if (statusBadge) {
            statusBadge.className = `badge ${getStatusBadgeClass(status)}`;
            statusBadge.textContent = status;
        }
    }

    function getStatusBadgeClass(status) {
        const statusClasses = {
            'Not Started': 'badge-secondary',
            'Ongoing': 'badge-primary',
            'Completed': 'badge-success',
            'On Hold': 'badge-warning'
        };
        return statusClasses[status] || 'badge-secondary';
    }

    // Helper functions
    function validateProjectDetails() {
        const requiredFields = projectDetailsContainer.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value) {
                field.classList.add('is-invalid');
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
            }
        });

        if (!isValid) {
            alert('Please fill in all required fields');
        }

        return isValid;
    }

    function validateSprints() {
        const sprintForms = document.querySelectorAll('.sprint-form');
        if (sprintForms.length === 0) {
            alert('Please generate at least one sprint');
            return false;
        }

        for (let form of sprintForms) {
            const scrumMaster = form.querySelector('[name="sprintScrumMaster[]"]').value;
            const startDate = form.querySelector('[name="sprintStartDate[]"]').value;
            const endDate = form.querySelector('[name="sprintEndDate[]"]').value;

            if (!scrumMaster || !startDate || !endDate) {
                alert('Please fill in all required sprint fields');
                return false;
            }
        }

        return true;
    }

    function generateSprintForms(count) {
        const container = document.getElementById('sprintsContainer');
        container.innerHTML = '';

        const projectStartDate = new Date(document.getElementById('startDate').value);
        const projectEndDate = new Date(document.getElementById('endDate').value);
        const sprintDuration = Math.floor((projectEndDate - projectStartDate) / (count * 86400000));

        for (let i = 1; i <= count; i++) {
            const sprintStartDate = new Date(projectStartDate);
            sprintStartDate.setDate(sprintStartDate.getDate() + (i-1) * sprintDuration);
            const sprintEndDate = new Date(sprintStartDate);
            sprintEndDate.setDate(sprintEndDate.getDate() + sprintDuration - 1);

            container.innerHTML += `
                <div class="sprint-form" data-sprint-number="${i}">
                    <h4>Sprint ${i}</h4>
                    <div class="form-group">
                        <label>Sprint Number</label>
                        <input type="number" class="form-control" name="sprintNumber[]" value="${i}" readonly>
                    </div>
                    <div class="form-group">
                        <label>Scrum Master</label>
                        <select class="form-control" name="sprintScrumMaster[]" required>
                            <option value="" disabled selected>Select Scrum Master</option>
                            ${generateTeamMemberOptions()}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Start Date</label>
                        <input type="date" class="form-control" name="sprintStartDate[]"
                               value="${sprintStartDate.toISOString().split('T')[0]}" required>
                    </div>
                    <div class="form-group">
                        <label>End Date</label>
                        <input type="date" class="form-control" name="sprintEndDate[]"
                               value="${sprintEndDate.toISOString().split('T')[0]}" required>
                    </div>
                     <div class="form-group">
                        <label>Status</label>
                        <select class="form-control" name="sprintStatus[]" required>
                            <option value="pending">Pending</option>
                            <option value="ongoing">Ongoing</option>
                            <option value="completed">Completed</option>
                            <option value="Not Started">Not Started</option>
                        </select>
                    </div>
                </div>
            `;
        }

        // Add event listeners for date validation
        addSprintDateValidation();
    }

    function generateStoryForms(count) {
        const container = document.getElementById('storiesContainer');
        container.innerHTML = '';

        // Fetch the number of sprints generated
        const sprintForms = document.querySelectorAll('.sprint-form');
        let sprintOptions = '<option value="" disabled selected>Select Sprint</option>';

        sprintForms.forEach((sprint, index) => {
            sprintOptions += `<option value="${index + 1}">${index + 1}</option>`;
        });

        for (let i = 1; i <= count; i++) {
            container.innerHTML += `
                <div class="story-form">
                    <h4>User Story ${i}</h4>
                    <div class="form-group">
                        <label>Team</label>
                        <select class="form-control" name="userStoryTeam[]" required>
                            <option value="" disabled selected>Select Team</option>
                            <option value="Team 1">Team 1</option>
                            <option value="Team 2">Team 2</option>
                            <option value="Team 3">Team 3</option>
                            <option value="Team 4">Team 4</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>User Story Description</label>
                        <textarea class="form-control" name="userStoryDescription[]" rows="3"
                            placeholder="As a [user], I want to [action] so that [benefit]" required></textarea>
                    </div>

                    <div class="form-group">
                        <label>Select Sprint</label>
                        <select class="form-control sprint-dropdown" name="userStorySprint[]" required>
                            ${sprintOptions}
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Story Points</label>
                        <select class="form-control" name="storyPoints[]" required>
                            <option value="1">1</option>
                            <option value="2">2</option>
                            <option value="3">3</option>
                            <option value="5">5</option>
                            <option value="8">8</option>
                            <option value="13">13</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Status</label>
                        <select class="form-control" name="userStoryStatus[]" required>
                            <option value="pending">Pending</option>
                            <option value="ongoing">Ongoing</option>
                            <option value="completed">Completed</option>
                            <option value="Not Started">Not Started</option>
                        </select>
                    </div>
                </div>
            `;
        }
    }

    // Corrected generateTeamMemberOptions function
    function generateTeamMemberOptions() {
        let optionsHTML = '<option value="" disabled selected>Select Scrum Master</option>';

        // Check if scrumMastersData is defined and is an array
        if (typeof scrumMastersData !== 'undefined' && Array.isArray(scrumMastersData)) {
            scrumMastersData.forEach(function(scrumMaster) {
                optionsHTML += `<option value="${scrumMaster.name}">${scrumMaster.name}</option>`;
            });
        } else {
            console.warn('scrumMastersData is not defined or is not an array.');
        }

        return optionsHTML;
    }

    function generateProjectId() {
        const lastProjectId = parseInt(localStorage.getItem('lastProjectId') || '0');
        // Format the number with leading zero
        const formattedNumber = String(lastProjectId + 1).padStart(2, '0');
        const projectId = 'PRJ-' + formattedNumber;
        localStorage.setItem('lastProjectId', (lastProjectId + 1).toString());
        return projectId;
    }

    function submitProject(e) {
        e.preventDefault();

        // Show loading state
        const submitButton = document.querySelector('.btn-submit');
        const originalText = submitButton.innerHTML;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';
        submitButton.disabled = true;

        const formData = {
            projectId: generateProjectId(),
            projectName: document.getElementById('projectName').value,
            projectDescription: document.getElementById('projectDescription').value,
            ProductOwner: document.getElementById('ProductOwner').value,
            devTeam: getSelectedDevTeam(),
            startDate: document.getElementById('startDate').value,
            endDate: document.getElementById('endDate').value,
            revisedEndDate: document.getElementById('revisedEndDate').value || null,
            status: document.getElementById('status').value, // Make sure status is included
            sprints: getSprintsData(),
            userStories: getUserStoriesData()
        };

        fetch('/add_project', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccessMessage('Project created successfully!');
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 1500);
            } else {
                showError('Failed to create project: ' + data.message);
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('An error occurred while creating the project');
            submitButton.innerHTML = originalText;
            submitButton.disabled = false;
        });
    }

    function getSelectedDevTeam() {
        return Array.from(document.querySelectorAll('[name="devTeam"]:checked')).map(checkbox => checkbox.value);
    }

    function getSprintsData() {
        const sprints = [];
        const sprintForms = document.querySelectorAll('.sprint-form');

        sprintForms.forEach((form) => {
            const sprintNumber = parseInt(form.querySelector('[name="sprintNumber[]"]').value);

            sprints.push({
                sprint_number: sprintNumber,
                scrum_master: form.querySelector('[name="sprintScrumMaster[]"]').value,
                start_date: form.querySelector('[name="sprintStartDate[]"]').value,
                end_date: form.querySelector('[name="sprintEndDate[]"]').value,
                status: form.querySelector('[name="sprintStatus[]"]').value
            });
        });

        return sprints;
    }

    function getUserStoriesData() {
        const stories = [];
        const storyForms = document.querySelectorAll('.story-form');

        storyForms.forEach((form, index) => {
            stories.push({
                team: form.querySelector('[name="userStoryTeam[]"]').value,
                description: form.querySelector('[name="userStoryDescription[]"]').value,
                points: parseInt(form.querySelector('[name="storyPoints[]"]').value),
                status: form.querySelector('[name="userStoryStatus[]"]').value,
                sprint_id: form.querySelector('[name="userStorySprint[]"]').value
            });
        });

        return stories;
    }

    function showSuccessMessage(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success';
        alertDiv.role = 'alert';
        alertDiv.style.position = 'fixed';
        alertDiv.style.top = '20px';
        alertDiv.style.right = '20px';
        alertDiv.style.zIndex = '1000';
        alertDiv.innerHTML = message;
        document.body.appendChild(alertDiv);

        setTimeout(() => {
            alertDiv.remove();
        }, 3000);
    }

    function showError(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger';
        alertDiv.role = 'alert';
        alertDiv.style.position = 'fixed';
        alertDiv.style.top = '20px';
        alertDiv.style.right = '20px';
        alertDiv.style.zIndex = '1000';
        alertDiv.innerHTML = message;
        document.body.appendChild(alertDiv);

        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    function assignStoriesToSprint(sprintNumber) {
        // Create modal for story assignment
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'assignStoriesModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Assign Stories to Sprint ${sprintNumber}</h5>
                        <button type="button" class="close" data-dismiss="modal">×</button>
                    </div>
                    <div class="modal-body">
                        <div class="available-stories">
                            ${generateAvailableStoriesList()}
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-primary" onclick="confirmStoryAssignment(${sprintNumber})">
                            Assign Selected Stories
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        $(modal).modal('show');
    }

    function generateAvailableStoriesList() {
        const storyForms = document.querySelectorAll('.story-form');
        let html = '<div class="list-group">';

        storyForms.forEach((form, index) => {
            const description = form.querySelector('[name="userStoryDescription[]"]').value;
            const points = form.querySelector('[name="storyPoints[]"]').value;

            html += `
                <div class="list-group-item">
                    <div class="custom-control custom-checkbox">
                        <input type="checkbox" class="custom-control-input"
                               id="story-${index + 1}" data-story-id="${index + 1}">
                        <label class="custom-control-label" for="story-${index + 1}">
                            ${description} (${points} points)
                        </label>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        return html;
    }

    function confirmStoryAssignment(sprintNumber) {
        const selectedStories = Array.from(document.querySelectorAll('#assignStoriesModal input[type="checkbox"]:checked'))
            .map(checkbox => ({
                id: parseInt(checkbox.dataset.storyId),
                description: checkbox.nextElementSibling.textContent.trim()
            }));

        const sprintStoriesContainer = document.getElementById(`sprint-${sprintNumber}-stories`);
        sprintStoriesContainer.innerHTML = selectedStories.map(story => `
            <div class="assigned-story badge badge-info mr-2 mb-2" data-story-id="${story.id}">
                ${story.description}
                <button type="button" class="close ml-2"
                        onclick="removeAssignedStory(this, ${sprintNumber})">×</button>
            </div>
        `).join('');

        $('#assignStoriesModal').modal('hide');
        setTimeout(() => {
            document.getElementById('assignStoriesModal').remove();
        }, 500);
    }

    function removeAssignedStory(button, sprintNumber) {
        button.parentElement.remove();
    }

    function addSprintDateValidation() {
        const sprintForms = document.querySelectorAll('.sprint-form');

        sprintForms.forEach(form => {
            const startDate = form.querySelector('[name="sprintStartDate[]"]');
            const endDate = form.querySelector('[name="sprintEndDate[]"]');

            startDate.addEventListener('change', () => validateSprintDates(form));
            endDate.addEventListener('change', () => validateSprintDates(form));
        });
    }

    function validateSprintDates(form) {
        const startDate = new Date(form.querySelector('[name="sprintStartDate[]"]').value);
        const endDate = new Date(form.querySelector('[name="sprintEndDate[]"]').value);
        const projectStartDate = new Date(document.getElementById('startDate').value);
        const projectEndDate = new Date(document.getElementById('endDate').value);

        if (startDate < projectStartDate || endDate > projectEndDate) {
            showError('Sprint dates must be within project duration');
            return false;
        }

        if (startDate >= endDate) {
            showError('Sprint end date must be after start date');
            return false;
        }

        return true;
    }
});











