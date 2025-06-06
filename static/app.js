// Enhanced data loader with error handling
async function loadData() {
    try {
        // Show loading state
        document.querySelector('#trending-news').innerHTML = '<div class="loading">Loading data...</div>';
        document.querySelector('#headlines tbody').innerHTML = '<tr><td colspan="5">Loading...</td></tr>';
        
        const [headlines, stats] = await Promise.all([
            fetch('/api/headlines').then(response => {
                if (!response.ok) throw new Error('Headlines API failed');
                return response.json();
            }),
            fetch('/api/stats').then(response => {
                if (!response.ok) throw new Error('Stats API failed');
                return response.json();
            })
        ]);
        
        renderHeadlines(headlines);
        renderTopicChart(stats.topics);
        renderSentimentChart(stats.sentiment);
        renderTrendingNews(stats.top_trending);
        
    } catch (error) {
        console.error("Error loading data:", error);
        document.querySelector('#trending-news').innerHTML = `<div class="error">Error: ${error.message}</div>`;
        document.querySelector('#headlines tbody').innerHTML = `<tr><td colspan="5">Error loading data</td></tr>`;
    }
}

// Render headlines table
function renderHeadlines(headlines) {
    const tableBody = document.querySelector('#headlines tbody');
    tableBody.innerHTML = headlines.map(headline => `
        <tr>
            <td>
                <div class="headline-title">${headline.title}</div>
                <div class="headline-preview">${headline.title.substring(0, 80)}...</div>
            </td>
            <td>${headline.source}</td>
            <td><span class="topic-tag">${headline.topic}</span></td>
            <td class="sentiment sentiment-${headline.sentiment.toLowerCase()}">
                <i class="fas ${getSentimentIcon(headline.sentiment)}"></i>
                ${headline.sentiment}
            </td>
            <td>${new Date(headline.date).toLocaleDateString()}</td>
        </tr>
    `).join('');
}

// Get sentiment icon
function getSentimentIcon(sentiment) {
    switch(sentiment.toLowerCase()) {
        case 'positive': return 'fa-smile-beam';
        case 'negative': return 'fa-frown';
        default: return 'fa-meh';
    }
}

// Render topic chart with gradient effect
function renderTopicChart(topics) {
    const ctx = document.getElementById('topicChart').getContext('2d');
    
    // Sort topics and get top 7
    const sortedTopics = Object.entries(topics)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 7);
    
    const labels = sortedTopics.map(item => item[0]);
    const data = sortedTopics.map(item => item[1]);
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(139, 92, 246, 0.8)');
    gradient.addColorStop(1, 'rgba(99, 102, 241, 0.3)');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Headlines',
                data: data,
                backgroundColor: gradient,
                borderColor: 'rgba(99, 102, 241, 1)',
                borderWidth: 1,
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round(context.parsed.y / total * 100);
                            return `${context.parsed.y} headlines (${percentage}%)`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: '#94a3b8',
                        font: {
                            size: 12
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#94a3b8',
                        font: {
                            size: 11,
                            weight: 'bold'
                        }
                    }
                }
            }
        }
    });
}

// Render sentiment chart with animation
function renderSentimentChart(sentiment) {
    const ctx = document.getElementById('sentimentChart').getContext('2d');
    
    // Sort sentiment for consistent colors
    const sortedSentiment = {
        Positive: sentiment.Positive || 0,
        Neutral: sentiment.Neutral || 0,
        Negative: sentiment.Negative || 0
    };
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(sortedSentiment),
            datasets: [{
                data: Object.values(sortedSentiment),
                backgroundColor: [
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(239, 68, 68, 0.8)'
                ],
                borderColor: [
                    'rgba(16, 185, 129, 1)',
                    'rgba(245, 158, 11, 1)',
                    'rgba(239, 68, 68, 1)'
                ],
                borderWidth: 2,
                hoverOffset: 20
            }]
        },
        options: {
            responsive: true,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#e2e8f0',
                        padding: 20,
                        font: {
                            size: 13,
                            weight: '500'
                        },
                        generateLabels: function(chart) {
                            const data = chart.data;
                            return data.labels.map((label, i) => {
                                const value = data.datasets[0].data[i];
                                const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                
                                return {
                                    text: `${label}: ${value} (${percentage}%)`,
                                    fillStyle: data.datasets[0].backgroundColor[i],
                                    strokeStyle: data.datasets[0].borderColor[i],
                                    hidden: false,
                                    index: i
                                };
                            });
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((context.parsed / total) * 100);
                            return `${context.label}: ${context.parsed} (${percentage}%)`;
                        }
                    }
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true
            }
        }
    });
}

// Render trending news cards with dynamic effects
function renderTrendingNews(trending) {
    const container = document.getElementById('trending-news');
    
    if (!trending || trending.length === 0) {
        container.innerHTML = '<div class="no-data">No trending news found</div>';
        return;
    }
    
    container.innerHTML = trending.slice(0, 5).map(news => `
        <div class="trend-card">
            <div class="topic-badge">${news.topic}</div>
            <h3>${news.title}</h3>
            <div class="sentiment sentiment-${news.sentiment.toLowerCase()}">
                <i class="fas ${getSentimentIcon(news.sentiment)}"></i>
                ${news.sentiment}
            </div>
            <div class="count">${news.count} mentions</div>
            <div class="source">${news.source}</div>
        </div>
    `).join('');
}

// Add additional styles dynamically
const dynamicStyles = document.createElement('style');
dynamicStyles.innerHTML = `
    .loading, .error, .no-data {
        text-align: center;
        padding: 2rem;
        grid-column: 1 / -1;
        font-size: 1.2rem;
    }
    
    .headline-title {
        font-weight: 600;
        margin-bottom: 5px;
    }
    
    .headline-preview {
        font-size: 0.9rem;
        color: #94a3b8;
        display: none;
    }
    
    footer {
        text-align: center;
        margin-top: 3rem;
        padding: 1.5rem;
        color: #64748b;
        font-size: 0.9rem;
        border-top: 1px solid #334155;
    }
    
    @media (min-width: 768px) {
        .headline-preview {
            display: block;
        }
    }
`;
document.head.appendChild(dynamicStyles);

// Initialize the dashboard
loadData();

// Add this to your existing app.js
function initWatermarkAnimation() {
    const watermark = document.querySelector('.watermark');
    watermark.innerHTML += ' ';
    
    // Create dynamic watermark text effect
    const watermarkText = 'AI News Trend Analyzer';
    let counter = 0;
    
    const interval = setInterval(() => {
        if (counter < watermarkText.length) {
            watermark.querySelector('span').textContent += watermarkText[counter];
            counter++;
        } else {
            clearInterval(interval);
        }
    }, 100);
}

// Call this function at the end of your app.js
document.addEventListener('DOMContentLoaded', () => {
    // ... your existing code ...
    
    // Initialize watermark animation
    initWatermarkAnimation();
    
    // Add profile photo hover effect
    const profilePhoto = document.querySelector('.profile-photo');
    if (profilePhoto) {
        profilePhoto.addEventListener('mouseenter', () => {
            profilePhoto.style.transform = 'scale(1.05) rotate(5deg)';
        });
        
        profilePhoto.addEventListener('mouseleave', () => {
            profilePhoto.style.transform = 'scale(1) rotate(0deg)';
        });
    }
});

// Refresh data every 5 minutes
setInterval(loadData, 300000);