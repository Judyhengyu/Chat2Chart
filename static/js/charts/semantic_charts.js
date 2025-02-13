/**
 * 语义分析图表
 */

// 关键词云图
function initKeywordsCloud(data) {
    const chart = echarts.init(document.getElementById('keywordsCloud'));

    // 检查数据格式
    if (!data || !data.tfidf) {
        console.error('Invalid keywords data:', data);
        return;
    }

    const option = {
        title: {
            text: '关键词云图',
            left: 'center'
        },
        tooltip: {
            show: true
        },
        series: [{
            type: 'wordCloud',
            shape: 'circle',
            left: 'center',
            top: 'center',
            width: '70%',
            height: '80%',
            right: null,
            bottom: null,
            sizeRange: [12, 60],
            rotationRange: [-90, 90],
            rotationStep: 45,
            gridSize: 8,
            drawOutOfBound: false,
            textStyle: {
                fontFamily: 'sans-serif',
                fontWeight: 'bold',
                color: function () {
                    return 'rgb(' + [
                        Math.round(Math.random() * 160),
                        Math.round(Math.random() * 160),
                        Math.round(Math.random() * 160)
                    ].join(',') + ')';
                }
            },
            emphasis: {
                focus: 'self',
                textStyle: {
                    shadowBlur: 10,
                    shadowColor: '#333'
                }
            },
            data: data.tfidf.map(([word, weight]) => ({
                name: word,
                value: weight * 10000
            }))
        }]
    };

    chart.setOption(option);
}

// 话题分布图
function initTopicsChart(data) {
    const chart = echarts.init(document.getElementById('topicsChart'));

    // 检查数据格式
    if (!data || !data.keywords) {
        console.error('Invalid topics data:', data);
        return;
    }

    // 获取前10个关键词和它们的频率
    const topKeywords = data.keywords.slice(0, 10);
    const frequencies = data.topic_frequencies || topKeywords.map((_, index) => {
        // 如果没有频率数据，使用递减的固定值
        return Math.round(100 * (1 - index * 0.08));
    });

    const option = {
        title: {
            text: '话题分布',
            left: 'center'
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: topKeywords,
            axisLabel: {
                interval: 0,
                rotate: 30
            }
        },
        yAxis: {
            type: 'value',
            name: '出现频率'
        },
        series: [{
            name: '话题频率',
            type: 'bar',
            data: frequencies,
            itemStyle: {
                color: function (params) {
                    // 使用渐变色
                    const colors = ['#83bff6', '#188df0', '#188df0', '#83bff6'];
                    return {
                        type: 'linear',
                        x: 0,
                        y: 0,
                        x2: 0,
                        y2: 1,
                        colorStops: [{
                            offset: 0, color: colors[0]
                        }, {
                            offset: 1, color: colors[1]
                        }]
                    }
                }
            }
        }]
    };

    chart.setOption(option);
}

// 情感分析图
function initSentimentChart(data) {
    const chart = echarts.init(document.getElementById('sentimentChart'));

    // 检查数据格式
    if (!data || typeof data.positive === 'undefined') {
        console.error('Invalid sentiment data:', data);
        return;
    }

    const option = {
        title: {
            text: '情感分布分析',
            left: 'center'
        },
        tooltip: {
            trigger: 'item',
            formatter: '{b}: {c}%'
        },
        legend: {
            orient: 'horizontal',
            bottom: '5%',
            left: 'center'
        },
        series: [
            {
                name: '情感分布',
                type: 'pie',
                radius: ['40%', '70%'],
                avoidLabelOverlap: false,
                itemStyle: {
                    borderRadius: 10,
                    borderColor: '#fff',
                    borderWidth: 2
                },
                label: {
                    show: true,
                    formatter: '{b}: {c}%',
                    position: 'outside'
                },
                emphasis: {
                    label: {
                        show: true,
                        fontSize: '18',
                        fontWeight: 'bold'
                    }
                },
                data: [
                    {
                        value: data.positive,
                        name: '积极',
                        itemStyle: {color: '#91cc75'}  // 绿色
                    },
                    {
                        value: data.neutral,
                        name: '中性',
                        itemStyle: {color: '#fac858'}  // 黄色
                    },
                    {
                        value: data.negative,
                        name: '消极',
                        itemStyle: {color: '#ee6666'}  // 红色
                    }
                ]
            }
        ]
    };

    chart.setOption(option);
}

// 话题标签追踪图
function initTagTrendsChart(data) {
    const chart = echarts.init(document.getElementById('tagTrendsChart'));

    // 检查数据格式
    if (!data || !data.trends) {
        console.error('Invalid tag trends data:', data);
        return;
    }

    // 基础话题标签和情感态度标签的颜色映射
    const basicTopicColors = {
        '工作': '#5470c6',
        '学习': '#91cc75',
        '生活': '#fac858',
        '娱乐': '#ee6666',
        '旅行': '#73c0de',
        '购物': '#3ba272',
        '健康': '#fc8452',
        '家庭': '#9a60b4',
        '朋友': '#ea7ccc',
        '财务': '#5470c6'
    };

    const emotionColors = {
        '开心': '#91cc75',
        '难过': '#ee6666',
        '生气': '#fc8452',
        '惊讶': '#fac858',
        '期待': '#73c0de',
        '支持': '#3ba272',
        '反对': '#ea7ccc',
        '建议': '#9a60b4',
        '抱怨': '#5470c6',
        '鼓励': '#91cc75'
    };

    const timeData = data.trends.times;
    const basicTopicData = data.trends.basicTopics;
    const emotionData = data.trends.emotions;

    // 处理数据：将每个时间点的标签转换为出现/未出现
    const processedData = [];
    for (let i = 0; i < timeData.length; i++) {
        const time = timeData[i];
        const tags = [];

        // 检查基础话题标签
        for (const [topic, counts] of Object.entries(basicTopicData)) {
            if (counts[i] > 0) {
                tags.push(topic);
            }
        }

        // 检查情感态度标签
        for (const [emotion, counts] of Object.entries(emotionData)) {
            if (counts[i] > 0) {
                tags.push(emotion);
            }
        }

        processedData.push({
            time: time,
            tags: tags,
            index: i
        });
    }

    // 生成散点图数据
    const scatterData = [];
    processedData.forEach(data => {
        data.tags.forEach(tag => {
            scatterData.push({
                value: [data.index, tag],
                itemStyle: {
                    color: basicTopicColors[tag] || emotionColors[tag]
                }
            });
        });
    });

    const option = {
        title: {
            text: '话题标签追踪',
            left: 'center',
            top: 5
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'line'
            },
            formatter: function (params) {
                const time = params[0].axisValue;
                const data = processedData.find(d => d.time === time);
                if (!data || !data.tags.length) return time + '<br/>无标签';

                let result = time + '<br/>';
                const basicTags = data.tags.filter(tag => tag in basicTopicColors);
                const emotionTags = data.tags.filter(tag => tag in emotionColors);

                if (basicTags.length > 0) {
                    result += '<div style="margin: 10px 0;"><strong>基础话题：</strong><br/>';
                    basicTags.forEach(tag => {
                        result += `<span style="display:inline-block;width:10px;height:10px;background:${basicTopicColors[tag]};margin-right:5px;"></span>${tag}<br/>`;
                    });
                    result += '</div>';
                }

                if (emotionTags.length > 0) {
                    result += '<div style="margin: 10px 0;"><strong>情感态度：</strong><br/>';
                    emotionTags.forEach(tag => {
                        result += `<span style="display:inline-block;width:10px;height:10px;background:${emotionColors[tag]};margin-right:5px;"></span>${tag}<br/>`;
                    });
                    result += '</div>';
                }

                return result;
            }
        },
        legend: {
            type: 'scroll',
            orient: 'horizontal',
            top: 30,
            left: 'center',
            data: [...Object.keys(basicTopicColors), ...Object.keys(emotionColors)]
        },
        toolbox: {
            feature: {
                dataZoom: {
                    yAxisIndex: 'none'
                },
                restore: {},
                saveAsImage: {}
            },
            right: '5%'
        },
        dataZoom: [
            {
                type: 'inside',
                start: 0,
                end: 100
            },
            {
                start: 0,
                end: 100,
                bottom: '5%'
            }
        ],
        grid: {
            left: '2%',
            right: '2%',
            bottom: '5%',
            top: '5%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: timeData,
            axisLabel: {
                rotate: 45,
                interval: 'auto',
                align: 'center'
            }
        },
        yAxis: {
            type: 'category',
            data: [...Object.keys(basicTopicColors), ...Object.keys(emotionColors)],
            axisLabel: {
                interval: 0,
                align: 'right'
            }
        },
        series: [{
            type: 'scatter',
            symbolSize: 15,
            data: scatterData,
            center: ['50%', '50%']
        }]
    };

    chart.setOption(option);

    // 监听窗口大小变化，自动调整图表大小
    window.addEventListener('resize', function () {
        chart.resize();
    });
} 