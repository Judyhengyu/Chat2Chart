/**
 * 基础分析图表
 */

// 消息类型统计饼图
function initMessageStatsChart(data) {
    const chart = echarts.init(document.getElementById('messageStatsChart'));
    const option = {
        title: {text: '消息类型分布', left: 'center'},
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {orient: 'vertical', left: 'left'},
        series: [{
            name: '消息类型',
            type: 'pie',
            radius: '50%',
            data: Object.entries(data.type_counts).map(([name, value]) => ({
                name, value
            })),
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        }]
    };
    chart.setOption(option);
}

// 时间分布图
function initTimeDistributionChart(data) {
    const chart = echarts.init(document.getElementById('timeDistributionChart'));
    const option = {
        title: {text: '消息时间分布', left: 'center'},
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
        xAxis: [{
            type: 'category',
            data: Array.from({length: 24}, (_, i) => `${i}时`),
            axisTick: {alignWithLabel: true}
        }],
        yAxis: [{type: 'value', name: '消息数量'}],
        series: [{
            name: '消息数量',
            type: 'bar',
            barWidth: '60%',
            data: Array.from({length: 24}, (_, i) => data.hourly_counts[i] || 0)
        }]
    };
    chart.setOption(option);
}

// 每日统计图
function initDailyStatsChart(data) {
    const chart = echarts.init(document.getElementById('dailyStatsChart'));
    const dates = Object.keys(data.daily_counts).sort();
    const messageTypes = Object.keys(data.daily_types);

    const series = messageTypes.map(type => ({
        name: type,
        type: 'line',
        stack: 'Total',
        areaStyle: {},
        emphasis: {focus: 'series'},
        data: dates.map(date => data.daily_types[type]?.[date] || 0)
    }));

    const option = {
        title: {text: '每日消息统计', left: 'center'},
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross',
                label: {backgroundColor: '#6a7985'}
            }
        },
        legend: {data: messageTypes, top: 30},
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: [{
            type: 'category',
            boundaryGap: false,
            data: dates
        }],
        yAxis: [{type: 'value', name: '消息数量'}],
        series: series
    };
    chart.setOption(option);
}

// 星期分布环状图
function initWeekdayChart(data) {
    const chart = echarts.init(document.getElementById('weekdayChart'));
    const weekdayMap = {
        'Monday': '周一', 'Tuesday': '周二', 'Wednesday': '周三',
        'Thursday': '周四', 'Friday': '周五', 'Saturday': '周六',
        'Sunday': '周日'
    };

    const weekdayData = Object.entries(data.weekday_counts).map(([key, value]) => ({
        name: weekdayMap[key] || key,
        value: value
    }));

    const option = {
        title: {
            text: '星期分布',
            left: 'center',
            top: 0,
            textStyle: {fontSize: 14}
        },
        tooltip: {
            trigger: 'item',
            formatter: '{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'vertical',
            left: '5%',
            top: 'middle',
            itemWidth: 8,
            itemHeight: 8,
            itemGap: 6,
            textStyle: {fontSize: 11}
        },
        series: [{
            name: '星期分布',
            type: 'pie',
            radius: ['40%', '70%'],
            center: ['60%', '50%'],
            avoidLabelOverlap: false,
            itemStyle: {
                borderRadius: 4,
                borderColor: '#fff',
                borderWidth: 2
            },
            label: {show: false},
            emphasis: {
                label: {
                    show: true,
                    fontSize: '12',
                    fontWeight: 'bold'
                }
            },
            labelLine: {show: false},
            data: weekdayData,
            color: ['#4154f1', '#2eca6a', '#ff771d', '#dc3545', '#6f42c1', '#0dcaf0', '#ffc107']
        }]
    };
    chart.setOption(option);
}

// 消息长度分析图表
function initMessageLengthChart(data) {
    const chart = echarts.init(document.getElementById('messageLengthChart'));
    const textStats = data.text_length || {};
    const voiceStats = data.voice_length || {};
    const callStats = data.call_duration || {};
    const avgCallMinutes = Math.round(callStats.average / 60 * 10) / 10;

    const option = {
        title: {
            text: '消息长度分析',
            left: 'center',
            top: 0,
            textStyle: {fontSize: 14}
        },
        tooltip: {
            trigger: 'item',
            formatter: function (params) {
                if (params.seriesName === '通话时长') {
                    return `平均通话时长<br/>${avgCallMinutes}分钟<br/>通话次数: ${callStats.count}`;
                }
                const stats = params.seriesName === '文字消息' ? textStats : voiceStats;
                const unit = params.seriesName === '文字消息' ? '字' : '秒';
                const count = params.name.includes('我的') ? stats.sender_count : stats.receiver_count;
                return `${params.name}<br/>平均: ${params.value}${unit}<br/>消息数: ${count}`;
            }
        },
        legend: {
            orient: 'vertical',
            left: '5%',
            top: 'middle',
            itemWidth: 8,
            itemHeight: 8,
            itemGap: 6,
            textStyle: {fontSize: 11}
        },
        series: [{
            name: '文字消息',
            type: 'pie',
            radius: ['65%', '80%'],
            center: ['60%', '50%'],
            label: {
                show: true,
                position: 'inside',
                formatter: '{c}字'
            },
            data: [
                {name: '我的文字', value: textStats.sender_average || 0, itemStyle: {color: '#4154f1'}},
                {name: '对方文字', value: textStats.receiver_average || 0, itemStyle: {color: '#2eca6a'}}
            ]
        }, {
            name: '语音消息',
            type: 'pie',
            radius: ['40%', '55%'],
            center: ['60%', '50%'],
            label: {
                show: true,
                position: 'inside',
                formatter: '{c}秒'
            },
            data: [
                {name: '我的语音', value: voiceStats.sender_average || 0, itemStyle: {color: '#ff771d'}},
                {name: '对方语音', value: voiceStats.receiver_average || 0, itemStyle: {color: '#dc3545'}}
            ]
        }, {
            name: '通话时长',
            type: 'pie',
            radius: ['15%', '30%'],
            center: ['60%', '50%'],
            label: {
                show: true,
                position: 'inside',
                formatter: `${avgCallMinutes}分`
            },
            data: [{
                name: '平均通话',
                value: 1,
                itemStyle: {color: '#6f42c1'}
            }]
        }]
    };
    chart.setOption(option);
} 