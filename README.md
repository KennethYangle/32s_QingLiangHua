# 32s_QingLiangHua
32s结题飞行演示程序。动捕环境3机穿3环。

## 准备
* 飞机和环粘上动捕球，编号为`BUAA_0x`和`CIRCLE_0y`
* 修改`_scripts/zzfly_startup.sh`的`mav_id`，修改`motion_capture_system/mocap_pose/launch/mocap_vrpn.launch`的`vrpn_topic`
* 订阅动捕发布的话题，是否为`/vrpn_client_node/BUAA_{:02d}/pose`

## 使用
```
./_scripts/zzfly_startup.sh
```
