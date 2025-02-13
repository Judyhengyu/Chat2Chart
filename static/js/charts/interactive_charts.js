/**
 * 交互分析图表
 */

// 对话模式分析图
function initChatPatternChart(data) {
    const chart = echarts.init(document.getElementById('chatPatternChart'));

    // 定义固定的时间间隔类别（保持顺序）
    const timeCategories = [
        '1小时内', '1-2小时', '2-3小时', '3-4小时', '4-5小时',
        '5-6小时', '6-12小时', '12-24小时', '24小时以上'
    ];

    // 定义渐变色系
    const colors = [
        '#75ace6',  // 蓝色
        '#69eca2',  // 绿色
        '#ec9069',  // 橙色
        '#c03131',  // 红色
        'rgba(111,66,193,0.63)',  // 紫色
        '#fd7e14',  // 深橙色
        '#07ce82',  // 青绿色
        'rgba(232,62,140,0.69)',  // 粉色
        '#eace5f'   // 黄色
    ];

    const option = {
        title: {
            text: '对话间隔分析',
            left: 'center'
        },
        tooltip: {
            trigger: 'axis',
            formatter: params => `${params[0].name}<br/>数量: ${params[0].value}条`
        },
        legend: {
            data: ['对话间隔'],
            top: 30
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '15%',  // 增加底部空间以适应旋转的标签
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: timeCategories,
            axisLabel: {
                interval: 0,
                rotate: 45,  // 增加旋转角度
                fontSize: 11
            }
        },
        yAxis: {
            type: 'value',
            name: '对话数量'
        },
        series: [
            {
                name: '对话间隔',
                type: 'bar',
                data: timeCategories.map((category, index) => ({
                    value: data.chat_pattern.conversation_gaps.distribution[category] || 0,
                    itemStyle: {
                        color: colors[index]
                    }
                })),
                label: {
                    show: true,
                    position: 'top',
                    fontSize: 11,
                    formatter: '{c}条'
                },
                barWidth: '50%'  // 调整柱子宽度
            }
        ]
    };

    chart.setOption(option);
}

// 响应时间分析图
function initResponseTimeChart(data) {
    const chart = echarts.init(document.getElementById('responseTimeChart'));

    const option = {
        title: {
            text: '响应时间分布',
            left: 'center'
        },
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'vertical',
            left: 'left',
            top: 30
        },
        series: [
            {
                name: '响应时间',
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
                        fontSize: '20',
                        fontWeight: 'bold'
                    }
                },
                labelLine: {
                    show: false
                },
                data: Object.entries(data.response_time.response_distribution).map(([name, value]) => ({
                    name,
                    value
                }))
            }
        ]
    };

    chart.setOption(option);
}

// 聊天热力图
function initChatHeatmap(data) {
    if (!data.heatmap?.data) {
        console.error('Invalid heatmap data:', data);
        return;
    }

    const chart = echarts.init(document.getElementById('chatHeatmap'));

    // 获取所有年份
    const years = [...new Set(data.heatmap.data.map(item => item[0].substring(0, 4)))].sort();
    const currentYear = years[years.length - 1]; // 默认显示最近一年

    // 过滤当前年份的数据
    const currentYearData = data.heatmap.data.filter(item => item[0].startsWith(currentYear));

    const option = {
        title: {
            text: `聊天记录热力图 (${currentYear}年)`,
            left: 'center',
            // top: 20
        },
        tooltip: {
            position: 'top',
            formatter: p => `${p.data[0]}<br/>消息数：${p.data[1]}条`
        },
        visualMap: {
            type: 'piecewise',
            pieces: data.heatmap.pieces,
            orient: 'horizontal',
            right: 120,
            top: 2,
            itemGap: 5,
            itemWidth: 15,
            itemHeight: 15,
            textStyle: {
                fontSize: 12
            }
        },
        calendar: {
            top: 80,
            left: '5%',      // 左边距改为百分比
            right: '5%',     // 右边距改为百分比
            cellSize: 'auto',  // 自动计算单元格大小
            range: currentYear,
            itemStyle: {
                borderWidth: 2,
                borderColor: '#fff'
            },
            monthLabel: {
                formatter: '{M}月',
                fontSize: 12,
                color: '#666'
            },
            dayLabel: {
                firstDay: 1,
                fontSize: 12,
                color: '#666',
                formatter: day => ['日', '一', '二', '三', '四', '五', '六'][day]
            },
            yearLabel: {
                show: false
            },
            splitLine: {
                lineStyle: {
                    color: '#fff',
                    width: 2
                }
            }
        },
        series: [{
            type: 'heatmap',
            coordinateSystem: 'calendar',
            data: currentYearData,
            emphasis: {
                itemStyle: {
                    borderColor: '#333',
                    borderWidth: 2
                }
            }
        }]
    };

    chart.setOption(option);

    // 添加年份选择器
    addYearSelector(chart, option, years, currentYear, data);
}

// 添加年份选择器辅助函数
function addYearSelector(chart, option, years, currentYear, data) {
    const select = document.createElement('select');
    Object.assign(select.style, {
        position: 'absolute',
        right: '30px',
        top: '2px',
        zIndex: '100',
        padding: '2px 5px',
        borderRadius: '3px',
        border: '1px solid #ddd'
    });

    years.forEach(year => {
        const opt = document.createElement('option');
        opt.value = year;
        opt.text = year + '年';
        opt.selected = year === currentYear;
        select.appendChild(opt);
    });

    select.onchange = function () {
        const selectedYear = this.value;
        option.calendar.range = selectedYear;
        option.title.text = `聊天记录热力图 (${selectedYear}年)`;
        option.series[0].data = data.heatmap.data.filter(item =>
            item[0].startsWith(selectedYear)
        );
        chart.setOption(option);
    };

    const container = document.getElementById('chatHeatmap');
    if (!container.querySelector('select')) {
        container.appendChild(select);
    }
}

// 互动情况分析图
function initInteractionChart(data) {
    const chart = echarts.init(document.getElementById('interactionChart'));

    const option = {
        title: {
            text: '对话互动分析',
            left: 'center'
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            }
        },
        legend: {
            data: ['我', '对方'],
            top: 30
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: ['发起对话', '结束对话']
        },
        yAxis: {
            type: 'value',
            axisLabel: {
                formatter: '{value}%'
            }
        },
        series: [
            {
                name: '我',
                type: 'bar',
                data: [
                    data.interaction.initiator.sender_percent,
                    data.interaction.ender.sender_percent
                ],
                label: {
                    show: true,
                    formatter: '{c}%'
                }
            },
            {
                name: '对方',
                type: 'bar',
                data: [
                    data.interaction.initiator.receiver_percent,
                    data.interaction.ender.receiver_percent
                ],
                label: {
                    show: true,
                    formatter: '{c}%'
                }
            }
        ]
    };

    chart.setOption(option);
} 