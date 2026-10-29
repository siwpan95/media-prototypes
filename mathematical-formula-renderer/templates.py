"""
数学公式模板库 —— 为 CA 渲染引擎提供初始化、演化规则、颜色映射的数学表达式模板。
"""

FORMULA_TEMPLATES = {
    # ---- 初始化公式 ----
    'init': {
        '纯随机': {
            'description': '每个细胞随机初始值',
            'expression': 'random()',
            'notes': '产生完全随机的初始状态，适合生命游戏类规则'
        },
        '稀疏随机': {
            'description': '少量细胞被激活',
            'expression': '1 if random() > 0.8 else 0',
            'notes': '约20%的细胞为1，其余为0。经典Game of Life初始态'
        },
        '中心脉冲': {
            'description': '中心位置高值，向外衰减',
            'expression': 'exp(-((x-0.5)**2 + (y-0.5)**2) / 0.02)',
            'notes': '高斯分布脉冲，适合观察扩散/传播行为'
        },
        '正弦条纹': {
            'description': '水平和垂直正弦波叠加',
            'expression': '0.3 + 0.2 * sin(x*20) * cos(y*20)',
            'notes': '产生规则的条纹图案，适合反应扩散方程'
        },
        '棋盘格': {
            'description': '二值棋盘格图案',
            'expression': '(i + j) % 2',
            'notes': '交替的0和1，适合测试各向异性演化'
        },
        '全零': {
            'description': '全部初始化为0',
            'expression': '0.0',
            'notes': '纯黑初始态，适合分形迭代类规则'
        },
        '梯度': {
            'description': '从左到右线性梯度',
            'expression': 'x',
            'notes': '从0到1的平滑渐变，适合观察边界效应'
        },
        '同心环': {
            'description': '中心向外发散的同心圆环',
            'expression': '0.5 + 0.5 * sin(sqrt((x-0.5)**2 + (y-0.5)**2) * 30)',
            'notes': '产生波纹状的初始图案'
        },
        '双高斯斑点': {
            'description': '两个高斯亮斑',
            'expression': 'exp(-((x-0.35)**2+(y-0.5)**2)/0.01) + exp(-((x-0.65)**2+(y-0.5)**2)/0.01)',
            'notes': '两个亮斑相互扩散、干涉'
        },
        'Perlin噪声近似': {
            'description': '用三角函数近似噪声',
            'expression': '0.5*(sin(x*30)+sin(y*35)+sin((x+y)*25)+sin((x-y)*28))/4 + 0.5',
            'notes': '多层正弦叠加模拟噪声纹理'
        },
        '多核随机': {
            'description': '3-5个随机位置高斯核叠加',
            'expression': 'exp(-((x-0.25)**2+(y-0.3)**2)/0.008) + exp(-((x-0.7)**2+(y-0.6)**2)/0.01) + 0.5*exp(-((x-0.5)**2+(y-0.7)**2)/0.012)',
            'notes': '多个高斯核提供丰富的初始结构'
        },
        '螺旋波': {
            'description': '阿基米德螺旋波纹',
            'expression': '0.5 + 0.5 * sin(atan2(y-0.5, x-0.5) * 6 + sqrt((x-0.5)**2+(y-0.5)**2) * 25)',
            'notes': '从中心向外发散的螺旋波，适合激发介质类演化规则'
        },
        '分形噪声v2': {
            'description': '六层正弦叠加的复杂噪声纹理',
            'expression': '0.5 + 0.2*(sin(x*18)+sin(y*22)+sin((x+y)*25)+sin((x-y)*28)+sin(x*38+y*15)+sin(x*12-y*42))/6',
            'notes': '比 v1 更丰富的空间频率，产生类地形纹理'
        },
        '径向渐变': {
            'description': '从中心向外线性渐变',
            'expression': 'sqrt((x-0.5)**2 + (y-0.5)**2) * 1.4',
            'notes': '纯距离渐变，适合观察扩散对称性；配合环形扩散演化规则效果最佳'
        },
        '钻石格': {
            'description': '曼哈顿距离菱形图案',
            'expression': 'abs(x-0.5) + abs(y-0.5)',
            'notes': '产生菱形/钻石状等值线，适合测试各向异性演化'
        },
        '十字星': {
            'description': '两条细线交叉的十字图案',
            'expression': 'exp(-(x-0.5)**2/0.0008) + exp(-(y-0.5)**2/0.0008)',
            'notes': '极细的十字交叉线，观察各向异性扩散的理想初始态'
        },
        '蜂窝网格': {
            'description': '六边形蜂窝状图案（用网格坐标）',
            'expression': '0.5 + 0.5 * cos(i*2.094) * cos(j*1.814) * cos((i+j)*1.571)',
            'notes': '利用 i,j 索引生成的六边形网格纹理'
        },
        '漩涡场': {
            'description': '角度 + 半径的复合漩涡',
            'expression': '(atan2(y-0.5, x-0.5)/(2*3.14159) + 0.5) * (1 - sqrt((x-0.5)**2+(y-0.5)**2)*1.2)',
            'notes': '角度编码颜色 + 径向衰减，产生彩色漩涡效果'
        },
        '多重斑点': {
            'description': '5个不同位置和大小的随机高斯斑点',
            'expression': 'exp(-((x-0.3)**2+(y-0.3)**2)/0.005) + exp(-((x-0.7)**2+(y-0.3)**2)/0.005) + exp(-((x-0.5)**2+(y-0.7)**2)/0.008) + exp(-((x-0.2)**2+(y-0.7)**2)/0.006) + exp(-((x-0.8)**2+(y-0.65)**2)/0.007)',
            'notes': '5个大小各异的高斯斑点，产生丰富的相互作用'
        },
        '半面激活': {
            'description': '左半区域随机，右半区域为零',
            'expression': 'random() if x < 0.5 else 0.0',
            'notes': '观察波前从激活区向静止区的传播行为'
        },
        '莫尔条纹': {
            'description': '两套同心环叠加产生莫尔效应',
            'expression': '0.5 + 0.25 * (sin(sqrt((x-0.35)**2+(y-0.45)**2)*30) + sin(sqrt((x-0.65)**2+(y-0.55)**2)*28))',
            'notes': '两套不同中心的环系统叠加，产生莫尔干涉图案'
        },
        '闪电分叉': {
            'description': '随机分叉的闪电状图案',
            'expression': 'max(0.0, 1.0 - 12*abs(y - 0.45 - 0.12*sin(x*18) - 0.06*sin(x*37))) * random()',
            'notes': '模拟闪电分支结构，配合激发介质演化规则效果极佳'
        },
    },

    # ---- 演化规则公式 ----
    'evolution': {
        'Smooth Life': {
            'description': '连续版生命游戏，用sigmoid过渡',
            'expression': '1 / (1 + exp(-12 * (avg_n - 0.5)))',
            'variables': ['c', 'sum_n', 'avg_n', 'x', 'y', 't'],
            'notes': '平滑过渡的生命游戏，产生流动的有机图案'
        },
        'Game of Life': {
            'description': '经典康威生命游戏（二值化）',
            'expression': '(c==1 and (sum_n==2 or sum_n==3)) or (c==0 and sum_n==3)',
            'variables': ['c', 'sum_n'],
            'notes': 'B3/S23规则，但需要二值初始状态'
        },
        '反应扩散（Gray-Scott简化）': {
            'description': '简化的反应扩散方程',
            'expression': 'c + 0.16*(avg_n - c) + 0.045*c*(1-c) - 0.02*c',
            'variables': ['c', 'avg_n'],
            'notes': '产生斑点、条纹等图灵图案。改变系数可调行为'
        },
        '纯扩散': {
            'description': '简单热扩散方程',
            'expression': 'c + 0.2 * (avg_n - c)',
            'variables': ['c', 'avg_n'],
            'notes': '平滑扩散，最终趋向均匀。系数控制扩散速度'
        },
        '伪Mandelbrot迭代': {
            'description': '类分形迭代映射',
            'expression': '(c*c + (x-0.5)*3.5 + (y-0.5)*2.0) % 1.0',
            'variables': ['c', 'x', 'y'],
            'notes': '用取模模拟分形迭代，位置相关的混沌行为'
        },
        '激发介质': {
            'description': '可兴奋介质模型（Barkley启发）',
            'expression': 'c + 0.02*(avg_n - c) + 0.15*c*(c-0.1)*(1-c) - 0.03*(c-0.5)',
            'variables': ['c', 'avg_n'],
            'notes': '产生螺旋波和靶波，需要中心脉冲初始态'
        },
        '竞争扩散': {
            'description': '带竞争项的扩散',
            'expression': 'c + 0.3*(avg_n - c) - 0.1*c*(1-c)*(c-0.5)',
            'variables': ['c', 'avg_n'],
            'notes': '两相竞争，中间态不稳定，趋向0或1'
        },
        '湍流混合': {
            'description': '时空混沌混合',
            'expression': '(c + 0.5*avg_n + 0.1*sin(x*30+t*0.1)*sin(y*30+t*0.1)) / 2',
            'variables': ['c', 'avg_n', 'x', 'y', 't'],
            'notes': '空间和时间耦合的混沌混合'
        },
        '各向异性扩散': {
            'description': '方向敏感扩散 + 非线性',
            'expression': 'c + 0.2*(avg_n - c) + 0.05*sin(x*10)*c*(1-c)',
            'variables': ['c', 'avg_n', 'x', 'y'],
            'notes': '不同位置扩散速率不同，产生定向条纹'
        },
        '逻辑斯蒂映射耦合': {
            'description': '逻辑斯蒂映射在空间上的耦合',
            'expression': '3.99 * c * (1 - c) + 0.1*(avg_n - c)',
            'variables': ['c', 'avg_n'],
            'notes': '每个细胞是逻辑斯蒂映射，邻域耦合产生丰富时空图案'
        },
        'Lenia启发式生长': {
            'description': '双峰高斯生长函数（Lenia风格），两个最优激活窗口',
            'expression': 'c + 0.12 * (2*exp(-(avg_n-0.32)**2/0.004) - 1 + 2*exp(-(avg_n-0.58)**2/0.01) - 1)',
            'variables': ['c', 'avg_n'],
            'notes': '模仿Lenia的高斯生长函数，两个最佳邻域浓度产生增长；需配合圆形邻域核'
        },
        'SmoothLife双环': {
            'description': '双环邻域（内环存活+外环繁殖）的平滑近似',
            'expression': '1/(1+exp(-18*(avg_n-0.22))) * 1/(1+exp(18*(avg_n-0.42))) + 0.8*c*1/(1+exp(-14*(avg_n-0.18)))*1/(1+exp(14*(avg_n-0.36)))',
            'variables': ['c', 'avg_n'],
            'notes': '用两个sigmoid窗口模拟SmoothLife的内环外环行为，产生流动的类生命形态'
        },
        '反应扩散（斑点）': {
            'description': 'Gray-Scott斑点模式参数',
            'expression': 'c + 0.14*(avg_n - c) + 0.042*c*(1-c) - 0.018*c',
            'variables': ['c', 'avg_n'],
            'notes': '系数调优的斑点模式：产生移动、分裂的圆形斑点；需配合正弦条纹初始态'
        },
        '反应扩散（条纹）': {
            'description': 'Gray-Scott条纹/波浪模式参数',
            'expression': 'c + 0.2*(avg_n - c) + 0.048*c*(1-c) - 0.028*c',
            'variables': ['c', 'avg_n'],
            'notes': '系数调优的条纹模式：产生蜿蜒的条纹和波浪纹理'
        },
        '反应扩散（迷宫）': {
            'description': 'Gray-Scott迷宫/迷宫状模式参数',
            'expression': 'c + 0.24*(avg_n - c) + 0.055*c*(1-c) - 0.038*c',
            'variables': ['c', 'avg_n'],
            'notes': '系数调优的迷宫模式：产生错综复杂的迷宫状结构'
        },
        'BZ反应模拟': {
            'description': 'Belousov-Zhabotinsky振荡反应简化模型',
            'expression': 'c + 0.06*(avg_n-c) + 0.22*c*(c-0.28)*(1-c) - 0.025*(avg_n-0.5)',
            'variables': ['c', 'avg_n'],
            'notes': 'Oregonator启发式简化，产生靶波和螺旋波；需中心脉冲初始态'
        },
        'FitzHugh–Nagumo': {
            'description': '可兴奋介质FHN模型启发',
            'expression': 'c + 0.07*(avg_n-c) + 0.28*c*(c-0.18)*(1-c) - 0.035*(c-0.3)',
            'variables': ['c', 'avg_n'],
            'notes': 'FHN神经脉冲模型启发，适合中心脉冲/闪电初始态，产生传播波前'
        },
        '混沌耦合映射': {
            'description': '逻辑斯蒂混沌与扩散的强耦合',
            'expression': '3.95*c*(1-c) + 0.18*(avg_n-c) + 0.03*sin(c*22+t*0.12)',
            'variables': ['c', 'avg_n', 't'],
            'notes': '混沌映射在空间上的强扩散耦合，随时空演化产生复杂分形纹理'
        },
        '相位振荡网络': {
            'description': '耦合相位振荡器（Kuramoto启发）',
            'expression': '(c + 0.06 + 0.04*sin(avg_n*10) + 0.03*sin(t*0.08)) % 1.0',
            'variables': ['c', 'avg_n', 't'],
            'notes': '全局耦合振子网络，产生同步波和相变图案'
        },
        '对流湍流混合': {
            'description': '扩散 + 强对流 + 时空混沌',
            'expression': '(c + 0.35*avg_n + 0.1*sin(x*25+t*0.2)*cos(y*22-t*0.15)) / 2.15',
            'variables': ['c', 'avg_n', 'x', 'y', 't'],
            'notes': '强空间对流 + 时间脉动，产生类似流体湍流的图案'
        },
        '增长抑制竞争': {
            'description': '类似DLA的扩散限制增长',
            'expression': 'c + 0.22*(avg_n - c) * (1.0 - c*0.85)',
            'variables': ['c', 'avg_n'],
            'notes': '高浓度区域抑制新增长，产生枝晶状分形结构'
        },
        '三次非线性扩散': {
            'description': '带三次非线性的反应扩散（Allen-Cahn启发）',
            'expression': 'c + 0.2*(avg_n-c) + 0.08*c*(1-c)*(c-0.5)',
            'variables': ['c', 'avg_n'],
            'notes': 'Allen-Cahn方程启发，相分离动力学，产生清晰的区域边界'
        },
    },

    # ---- 颜色映射公式 ----
    'color': {
        '反转灰阶': {
            'description': '黑底白花（反转亮度）',
            'red': 'v', 'green': 'v', 'blue': 'v',
            'notes': '经典黑白显示，适合观察生命游戏等二值规则'
        },
        '暖色渐变': {
            'description': '暗红→亮黄渐变',
            'red': 'v',
            'green': 'v * 0.6',
            'blue': 'v * 0.1',
            'notes': '从黑到红到黄的暖色调'
        },
        '冷色渐变': {
            'description': '暗蓝→亮青渐变',
            'red': 'v * 0.2',
            'green': 'v * 0.7',
            'blue': 'v',
            'notes': '从黑到蓝到青的冷色调'
        },
        '彩虹': {
            'description': 'v值映射为彩虹色',
            'red': '0.5 + 0.5*sin(v*12)',
            'green': '0.5 + 0.5*sin(v*12 + 2.094)',
            'blue': '0.5 + 0.5*sin(v*12 + 4.189)',
            'notes': 'RGB三个通道相位差2pi/3，v从0到1走完彩虹'
        },
        '绿紫双色': {
            'description': '暗绿→亮紫渐变',
            'red': 'v * 0.8',
            'green': '1.0 - v * 0.7',
            'blue': 'v * 0.9',
            'notes': '非传统的双色方案，适合反应扩散'
        },
        '日落': {
            'description': '深蓝→橙红渐变',
            'red': 'v*0.9 + (1-v)*0.05',
            'green': 'v*0.3 + (1-v)*0.05',
            'blue': 'v*0.1 + (1-v)*0.3',
            'notes': '从夜空蓝渐变到日落橙'
        },
        '位置着色': {
            'description': '颜色随空间位置变化 + v值调亮度',
            'red': 'v * (0.5 + 0.5*sin(x*15))',
            'green': 'v * (0.5 + 0.5*sin(y*15))',
            'blue': 'v * (0.5 + 0.5*sin((x+y)*15))',
            'notes': '基于位置(hue) × 细胞值(brightness)的复合着色'
        },
        '二值锐化': {
            'description': '阈值二分 → 只有纯黑纯白',
            'red': '1 if v > 0.5 else 0',
            'green': '1 if v > 0.5 else 0',
            'blue': '1 if v > 0.5 else 0',
            'notes': '只显示纯黑和纯白，锐化边界'
        },
        '霓虹热感': {
            'description': '黑→红→黄→白热力图',
            'red': 'min(v*3, 1.0)',
            'green': 'max(0, min((v-0.33)*3, 1.0))',
            'blue': 'max(0, (v-0.66)*3)',
            'notes': '经典热力图颜色映射'
        },
        '极光': {
            'description': '绿紫极光渐变',
            'red': 'v*0.1 + 0.5*sin(v*8)*v',
            'green': 'v*0.35 + 0.45*sin(v*6+2)*v',
            'blue': 'v*0.65 + 0.3*sin(v*5+4)*v',
            'notes': '模仿北极光，从暗绿过渡到亮紫'
        },
        '深海': {
            'description': '深海蓝绿色调',
            'red': 'v*0.05',
            'green': 'v*0.35 + 0.15*sin(v*8)*v',
            'blue': 'v*0.75 + 0.15*cos(v*6)*v',
            'notes': '深邃的海洋色调，低值近黑、高值亮蓝'
        },
        '熔岩': {
            'description': '黑→暗红→橙黄渐变',
            'red': 'v',
            'green': 'v*v*0.7',
            'blue': 'v*v*v*0.12',
            'notes': '幂律映射产生熔岩般的强烈暖色调'
        },
        '赛博朋克': {
            'description': '霓虹紫 + 青色赛博朋克风格',
            'red': 'v*0.75 + 0.25*sin(v*9)*v',
            'green': 'v*0.1 + 0.22*sin(v*6+3)*v',
            'blue': 'v*0.85 + 0.15*sin(v*7+1)*v',
            'notes': '紫-青双色，适合科技感视觉表现'
        },
        '金属金': {
            'description': '暗铜→金色金属质感',
            'red': 'v*0.92 + 0.08*sin(v*14)',
            'green': 'v*0.58 + 0.18*sin(v*11+1)',
            'blue': 'v*0.08 + 0.05*sin(v*9+2)',
            'notes': '金色金属光泽，低值偏暗铜色'
        },
        '秋叶': {
            'description': '深棕→橙色→金黄秋叶色调',
            'red': 'v*0.95 + (1-v)*0.04',
            'green': 'v*0.32 + (1-v)*0.02',
            'blue': 'v*0.06 + (1-v)*0.01',
            'notes': '温暖的秋季色调，适合有机图案'
        },
        '紫色梦境': {
            'description': '靛蓝→紫罗兰→品红梦幻渐变',
            'red': 'v*0.65 + 0.35*sin(v*5.5)*v',
            'green': 'v*0.04',
            'blue': 'v*0.85 + 0.12*cos(v*6.5)*v',
            'notes': '极低绿色通道，产生纯净的紫蓝色渐变'
        },
        '冰川': {
            'description': '冰蓝→白色冷冻色调',
            'red': 'v*0.55 + 0.35*sin(v*2.5)',
            'green': 'v*0.72 + 0.2*cos(v*3.5)',
            'blue': 'v*0.9 + 0.1*sin(v*1.8)',
            'notes': '冷色调白-蓝渐变，低值偏暗蓝、高值亮白'
        },
    }
}


def print_template(template_type='all'):
    """打印公式模板到控制台"""
    types = ['init', 'evolution', 'color'] if template_type == 'all' else [template_type]

    for t in types:
        if t not in FORMULA_TEMPLATES:
            print(f"  [未知模板类型: {t}]")
            continue

        type_names = {'init': '初始化公式', 'evolution': '演化规则公式', 'color': '颜色映射公式'}
        print(f"\n{'='*60}")
        print(f"  {type_names.get(t, t)}模板")
        print(f"{'='*60}")

        for name, info in FORMULA_TEMPLATES[t].items():
            print(f"\n  ◆ {name}")
            print(f"    说明: {info['description']}")
            if 'expression' in info:
                print(f"    公式: {info['expression']}")
            if 'variables' in info:
                print(f"    变量: {', '.join(info['variables'])}")
            if 'red' in info:
                print(f"    R通道: {info['red']}")
                print(f"    G通道: {info['green']}")
                print(f"    B通道: {info['blue']}")
            print(f"    提示: {info['notes']}")


def list_all_templates():
    """列出所有模板名称"""
    print("\n===== 初始化公式模板 =====")
    for name in FORMULA_TEMPLATES['init']:
        print(f"  {name}")
    print("\n===== 演化规则模板 =====")
    for name in FORMULA_TEMPLATES['evolution']:
        print(f"  {name}")
    print("\n===== 颜色映射模板 =====")
    for name in FORMULA_TEMPLATES['color']:
        print(f"  {name}")
    print(f"\n共 {sum(len(v) for v in FORMULA_TEMPLATES.values())} 个模板")
