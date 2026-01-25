/**
 * Route Wizard Alpine.js Component
 * Manages route generation and display logic
 */
function routeWizard(availableTags, isAuthenticated) {
    return {
        // State management
        mode: 'ai', // 'ai' | 'manual'
        tags: availableTags || [],
        selectedTags: [],
        description: '',
        isGenerating: false,
        generatedRoute: null,
        error: null,
        showAuthModal: false,
        isSaving: false,
        
        // Route result state
        activeView: 'list', // 'list' | 'map' (mobile only)
        expandedPointId: null,
        mapInstance: null,
        markers: [],
        
        // Computed properties
        get isFormValid() {
            return this.selectedTags.length >= 1 && 
                   this.selectedTags.length <= 3 &&
                   this.description.length <= 10000;
        },
        
        /**
         * Toggle tag selection
         */
        toggleTag(tagId) {
            const index = this.selectedTags.indexOf(tagId);
            if (index > -1) {
                // Remove tag
                this.selectedTags.splice(index, 1);
            } else {
                // Add tag if under limit
                if (this.selectedTags.length < 3) {
                    this.selectedTags.push(tagId);
                }
            }
            
            // Clear tag-specific errors
            if (this.error && this.error.tags) {
                this.error.tags = null;
            }
        },
        
        /**
         * Generate route via API
         */
        async generateRoute() {
            // Check authentication
            if (!isAuthenticated) {
                this.showAuthModal = true;
                return;
            }
            
            // Validate form
            if (!this.isFormValid) {
                return;
            }
            
            this.isGenerating = true;
            this.error = null;
            
            try {
                const headers = {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),
                };
                
                // Add auth token if available (for API authentication)
                const authToken = localStorage.getItem('authToken');
                if (authToken) {
                    headers['Authorization'] = `Token ${authToken}`;
                }
                
                const response = await fetch('/api/routes/', {
                    method: 'POST',
                    headers: headers,
                    credentials: 'include',
                    body: JSON.stringify({
                        route_type: 'ai_generated',
                        tags: this.selectedTags,
                        description: this.description || null,
                    }),
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    // Handle validation errors
                    if (response.status === 400) {
                        this.error = {
                            general: 'Wystąpił błąd walidacji. Sprawdź wprowadzone dane.',
                            ...data
                        };
                    } else if (response.status === 401) {
                        this.showAuthModal = true;
                    } else {
                        this.error = {
                            general: data.detail || 'Wystąpił błąd podczas generowania trasy.'
                        };
                    }
                    return;
                }
                
                // Success - store generated route
                this.generatedRoute = data;
                
                // Initialize map after route is set
                this.$nextTick(() => {
                    this.initMap();
                });
                
            } catch (err) {
                console.error('Route generation error:', err);
                this.error = {
                    general: 'Wystąpił błąd połączenia. Spróbuj ponownie.'
                };
            } finally {
                this.isGenerating = false;
            }
        },
        
        /**
         * Initialize Leaflet map
         */
        initMap() {
            if (!this.generatedRoute || !this.generatedRoute.points || this.generatedRoute.points.length === 0) {
                return;
            }
            
            // Clean up existing map
            if (this.mapInstance) {
                this.mapInstance.remove();
                this.markers = [];
            }
            
            const mapElement = document.getElementById('map');
            if (!mapElement) {
                return;
            }
            
            // Get center point (first point)
            const firstPoint = this.generatedRoute.points[0];
            const centerLat = firstPoint.place.lat;
            const centerLon = firstPoint.place.lon;
            
            // Initialize map
            this.mapInstance = L.map('map').setView([centerLat, centerLon], 13);
            
            // Add tile layer
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                maxZoom: 19,
            }).addTo(this.mapInstance);
            
            // Add markers for each point
            this.generatedRoute.points.forEach((point, index) => {
                const marker = L.marker([point.place.lat, point.place.lon])
                    .addTo(this.mapInstance)
                    .bindPopup(`
                        <div class="font-semibold">${index + 1}. ${point.place.name}</div>
                        ${point.place.address ? `<div class="text-sm">${point.place.address}</div>` : ''}
                    `);
                
                // Handle marker click
                marker.on('click', () => {
                    this.expandedPointId = point.id;
                    // Scroll to point in list view
                    this.scrollToPoint(point.id);
                });
                
                this.markers.push(marker);
            });
            
            // Draw polyline connecting points
            if (this.generatedRoute.points.length > 1) {
                const latlngs = this.generatedRoute.points.map(point => [
                    point.place.lat,
                    point.place.lon
                ]);
                L.polyline(latlngs, {
                    color: '#4F46E5',
                    weight: 3,
                    opacity: 0.7
                }).addTo(this.mapInstance);
            }
            
            // Fit bounds to show all markers
            const bounds = L.latLngBounds(
                this.generatedRoute.points.map(p => [p.place.lat, p.place.lon])
            );
            this.mapInstance.fitBounds(bounds, { padding: [50, 50] });
        },
        
        /**
         * Scroll to point in list view
         */
        scrollToPoint(pointId) {
            // This would be implemented with proper DOM manipulation
            console.log('Scroll to point:', pointId);
        },
        
        /**
         * Remove point from route
         */
        async removePoint(pointId) {
            if (!this.generatedRoute) {
                return;
            }
            
            // Remove from local state
            this.generatedRoute.points = this.generatedRoute.points.filter(
                p => p.id !== pointId
            );
            
            // Update map
            this.$nextTick(() => {
                this.initMap();
            });
            
            // TODO: Call API to update route on backend
        },
        
        /**
         * Save route permanently
         */
        async saveRoute() {
            if (!this.generatedRoute || !this.generatedRoute.id) {
                return;
            }
            
            this.isSaving = true;
            
            try {
                const headers = {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),
                };
                
                // Add auth token if available
                const authToken = localStorage.getItem('authToken');
                if (authToken) {
                    headers['Authorization'] = `Token ${authToken}`;
                }
                
                const response = await fetch(`/api/routes/${this.generatedRoute.id}/`, {
                    method: 'PATCH',
                    headers: headers,
                    credentials: 'include',
                    body: JSON.stringify({
                        status: 'saved',
                        name: 'Moja trasa' // TODO: Allow user to name the route
                    }),
                });
                
                if (response.ok) {
                    alert('Trasa została zapisana!');
                    // TODO: Redirect to user's routes list
                } else {
                    alert('Wystąpił błąd podczas zapisywania trasy.');
                }
            } catch (err) {
                console.error('Save route error:', err);
                alert('Wystąpił błąd połączenia.');
            } finally {
                this.isSaving = false;
            }
        },
        
        /**
         * Discard generated route
         */
        discardRoute() {
            if (confirm('Czy na pewno chcesz odrzucić tę trasę?')) {
                this.generatedRoute = null;
                this.expandedPointId = null;
                
                // Clean up map
                if (this.mapInstance) {
                    this.mapInstance.remove();
                    this.mapInstance = null;
                    this.markers = [];
                }
                
                // Reset form
                this.selectedTags = [];
                this.description = '';
            }
        },
        
        /**
         * Get CSRF token from cookie
         */
        getCsrfToken() {
            const name = 'csrftoken';
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
    };
}
