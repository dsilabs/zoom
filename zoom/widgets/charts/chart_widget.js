
var ctx = document.getElementById('$(( chart.uid ))');
var myChart = new Chart(ctx, {
    type: '$(( chart.type ))',
    data: {
        labels: $(( chart.labels )),
        datasets: [{
            label: false,
            data: $(( chart.data )),
            borderColor: '$(( chart.line_color ))',
            backgroundColor: '$(( chart.fill_color ))',
            pointBackgroundColor: '$(( chart.point_background_color ))',
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
                top: 0,
                right: 0,
                bottom: 0,
                left: 0,
            }
        },
        responsive: true,
        maintainAspectRatio: false,
        elements: {
            line: {
                borderWidth: 1,
                tension: $(( chart.line_tension )),
            },
            point: {
                radius: 4,
                hitRadius: 10,
                hoverRadius: 4
            }
        },
        scales: {
            xAxes: [{
                    display: false,
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
