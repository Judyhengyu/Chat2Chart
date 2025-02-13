/**
 * 仪表盘图表
 */

// 消息类型分布图
function initMessageTypesChart(data) {
    const chart = echarts.init(document.getElementById('messageTypesChart'));

    const option = {
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'vertical',
            left: 'left',
            type: 'scroll'
        },
        series: [
            {
                name: '消息类型',
                type: 'pie',
                radius: ['40%', '70%'],
                avoidLabelOverlap: false,
                itemStyle: {
                    borderRadius: 10,
                    borderColor: '#fff',
                    borderWidth: 2
                },
                label: {
                    show: false,
                    position: 'center'
                },
                emphasis: {
                    label: {
                        show: true,
                        fontSize: '18',
                        fontWeight: 'bold'
                    }
                },
                labelLine: {
                    show: false
                },
                data: Object.entries(data).map(([name, value]) => ({
                    name,
                    value
                }))
            }
        ]
    };

    chart.setOption(option);
}

// 活跃时段分布图
function initActiveTimeChart(data) {
    const chart = echarts.init(document.getElementById('activeTimeChart'));

    const hours = Array.from({length: 24}, (_, i) => i);

    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {type: 'shadow'}
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: [
            {
                type: 'category',
                data: hours.map(h => `${h}时`),
                axisTick: {
                    alignWithLabel: true
                }
            }
        ],
        yAxis: [
            {
                type: 'value',
                name: '消息数'
            }
        ],
        series: [
            {
                name: '消息数量',
                type: 'bar',
                barWidth: '60%',
                data: hours.map(hour => data[hour] || 0),
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        {offset: 0, color: '#83bff6'},
                        {offset: 0.5, color: '#188df0'},
                        {offset: 1, color: '#188df0'}
                    ])
                }
            }
        ]
    };

    chart.setOption(option);
} 