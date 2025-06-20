// 曼德布罗特集演示
// 支持鼠标滚轮无限放大缩小，鼠标点击中心定位
// 包含平滑着色和色彩增强效果

#define MAX_ITER 200    // 最大迭代次数
#define ESCAPE_RADIUS 4.0 // 逃逸半径平方

// 平滑着色函数
float smoothColor(float iter, vec2 z) {
    return iter - log2(log2(dot(z,z))) + 4.0;
}

// 调色板函数
vec3 palette(float t) {
    // 使用多个正弦波创建丰富的色彩过渡
    vec3 a = vec3(0.5, 0.5, 0.5);
    vec3 b = vec3(0.5, 0.5, 0.5);
    vec3 c = vec3(1.0, 1.0, 1.0);
    vec3 d = vec3(0.263, 0.416, 0.557);
    
    return a + b*cos(6.28318*(c*t+d));
}

// 主渲染函数
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // 初始化视图参数
    float zoom = pow(0.9, 1.0); // 使用鼠标滚轮控制缩放
    vec2 center = iMouse.xy/iResolution.xy * 2.0 - 1.0; // 鼠标点击位置作为中心
    
    // 调整中心点坐标以匹配屏幕比例
    center.x *= iResolution.x/iResolution.y;
    
    // 计算当前像素在复平面的坐标
    vec2 uv = (fragCoord.xy - 0.5*iResolution.xy) / (0.5*min(iResolution.x, iResolution.y)) * zoom;
    uv -= center;
    
    // 曼德布罗特集迭代
    vec2 c = uv;
    vec2 z = vec2(0.0);
    float iter = 0.0;
    
    for (int i = 0; i < MAX_ITER; i++) {
        z = vec2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
        if (dot(z,z) > ESCAPE_RADIUS) break;
        iter++;
    }
    
    // 计算颜色
    vec3 col;
    if (iter == float(MAX_ITER)) {
        col = vec3(0.0); // 集合内部为黑色
    } else {
        // 使用平滑着色
        float smoothed = smoothColor(iter, z);
        float t = smoothed / float(MAX_ITER);
        
        // 应用调色板
        col = palette(fract(t * 5.0 + 0.3));
        
        // 增强对比度
        col = pow(col, vec3(1.5));
        
        // 添加发光效果
        col *= 0.7 + 0.5*sin(t * 50.0);
    }
    
    // 添加坐标网格（在低缩放级别时可见）
    if (zoom < 5.0) {
        vec2 grid = abs(fract(uv * 2.0) - 0.5);
        float gridLine = smoothstep(0.02/zoom, 0.0, min(grid.x, grid.y));
        col = mix(col, vec3(0.3), gridLine * 0.3);
    }
    
    // 显示坐标信息（调试用）
    // col = mix(col, vec3(1.0,0,0), step(0.99, fract(uv.x)));
    // col = mix(col, vec3(0,1.0,0), step(0.99, fract(uv.y)));
    
    fragColor = vec4(col, 1.0);
}
