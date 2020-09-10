
var ctx = document.getElementById('$(( metric.uid ))');
var myChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: $(( metric.labels )),
        labels: $(( metric.labels )),
        datasets: [{
            data: $(( metric.data )),
            borderColor: '$(( metric.line_color ))',
            backgroundColor: '$(( metric.fill_color ))',
            pointBackgroundColor: '$(( metric.point_background_color ))',
            borderWidth: 1
        }]
    },
    options: {
        animation: {
            duration: 500
        },
        legend: {
            display: false
        },
        layout: {
            padding: {
                top: 5,
                right: 0,
                bottom: 5,
                left: 0,
            }
        },
        responsive: true,
        maintainAspectRatio: false,
        elements: {
            line: {
                borderWidth: 1
            },
            point: {
                radius: 4,
                hitRadius: 10,
                hoverRadius: 4
            }
        },
        scales: {
            xAxes: [{
                    gridLines: {
                        color: 'transparent',
                        zeroLineColor: 'transparent'
                    },
                    ticks: {
                        fontSize: 2,
                        fontColor: 'transparent'
                    }
            }],
            yAxes: [{
                display: false,
            }]
        }
    }
});