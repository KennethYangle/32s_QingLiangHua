## 一、环境
* `RflySim`仿真环境（可选，SITL仿真需要）
* `Python`环境（推荐Anaconda）中安装`pymavlink`


## 二、SITL仿真
### 1. 启动`RflySim`场景
双击`RflySim\GTASITL.bat`

### 2. 启动分配算法
```
python main.py
```
分配结果计算完成后会在终端打印统计信息，弹出示意图。

关掉图片之后，`RflySim`里也会创建对应的飞机和直接的关系。拖动到合适的视角，`Ctrl+滚轮放大飞机`，`S`键打开编号，即可得到论文中的效果。

终端按下任意键开始运动效果。


## 三、外部调用
```
# 示例
python main_ly.py
# 或者调用其中函数
useGTA(Pcur, ViewR, p_search)
```
输入：
* 各无人机位置`Pcur`，np.ndarray或list类型，尺寸 Nx3
* 观测半径`ViewR`，np.ndarray或list类型，尺寸 Nx1
* 待搜索坐标列表`p_search`，np.ndarray或list类型，尺寸 mx3

输出：
* 每一架无人机下一个目标位置`p_next`，np.ndarray或list类型，尺寸 Nx3


## 四、UDP调用
`main_UDP.py`和`UDP_test.py`，从9797端口输入数据，从9798端口返回结果
