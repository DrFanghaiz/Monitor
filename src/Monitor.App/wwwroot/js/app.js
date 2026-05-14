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
        '#4C8DFF',
        '#2E9D77',
        '#C2932E',
        '#C95F5F',
        '#4EA4B8',
        '#7F75C8',
        '#B9689C',
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
