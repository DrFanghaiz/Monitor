// ECharts interop
window.renderChart = (elementId, optionJson) => {
    const el = document.getElementById(elementId);
    if (!el) return;
    let chart = echarts.getInstanceByDom(el);
    if (!chart) {
        chart = echarts.init(el, null, { renderer: 'canvas' });
    }
    const option = JSON.parse(optionJson);
    option.backgroundColor ??= 'transparent';
    option.textStyle ??= { color: '#506176' };
    option.animation ??= true;
    option.animationDuration ??= 450;
    option.animationDurationUpdate ??= 220;
    option.animationEasing ??= 'cubicOut';
    option.animationEasingUpdate ??= 'cubicOut';
    option.color ??= [
        '#0A84FF',
        '#15996B',
        '#B7791F',
        '#D95050',
        '#3B9FB8',
        '#7C6BD6',
        '#C05B9C',
        '#8EA0B8'
    ];
    option.tooltip = {
        backgroundColor: '#FBFCFF',
        borderColor: '#CCD7E6',
        textStyle: { color: '#1D2938' },
        ...option.tooltip
    };
    chart.setOption(option, true);
    window.addEventListener('resize', () => chart.resize());
};

window.resizeChart = (elementId) => {
    const el = document.getElementById(elementId);
    if (!el) return;
    const chart = echarts.getInstanceByDom(el);
    if (chart) chart.resize();
};

window.destroyChart = (elementId) => {
    const el = document.getElementById(elementId);
    if (!el) return;
    const chart = echarts.getInstanceByDom(el);
    if (chart) chart.dispose();
};
