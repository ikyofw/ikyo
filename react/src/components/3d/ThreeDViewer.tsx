/*
 * @Description:
 * @version:
 * @Author: Sunny
 * @Date: 2022-07-14 17:25:11
 */
import React from "react"
import { GLTFModel, AmbientLight, DirectionLight } from "react-3d-viewer"

// const obj1 = require("./model2/PileVolumeModel1.glb")

interface ThreeDViewerProps {
  modelUrl: any

  //px
  disWidth?: string
  disHeight?: string
  scale?: ScaleProps
}

export interface ScaleProps {
  x: Number
  y: Number
  z: Number
}

const ThreeDViewer: React.FC<ThreeDViewerProps> = ({
  modelUrl,
  disWidth,
  disHeight,
  scale,
}) => {
  return (
    // <>
    <GLTFModel
      src={modelUrl}
      width={disWidth ? disWidth : window.innerWidth /* + AND - AS DESIRED*/}
      height={
        disHeight ? disHeight : window.innerHeight /* + AND - AS DESIRED*/
      }
      scale={scale ? scale : { x: 1, y: 1, z: 1 }}
    >
      <AmbientLight color={0xffffff} />
      <DirectionLight
        // color={0xffffff}
        castShadow={false}
        position={{ x: 10, y: 10, z: 100 }}
      />
      <DirectionLight
        // color={0xffffff}
        castShadow={false}
        position={{ x: -10, y: -10, z: 100 }}
      />
      <DirectionLight
        // color={0xffffff}
        castShadow={false}
        position={{ x: 10, y: -10, z: 100 }}
      />
      <DirectionLight
        // color={0xffffff}
        castShadow={false}
        position={{ x: -10, y: 10, z: 100 }}
      />
      <DirectionLight
        // color={0xffffff}
        castShadow={false}
        position={{ x: 10, y: 10, z: -100 }}
      />
      <DirectionLight
        // color={0xffffff}
        castShadow={false}
        position={{ x: -10, y: -10, z: -100 }}
      />
      <DirectionLight
        // color={0xffffff}
        castShadow={false}
        position={{ x: 10, y: -10, z: -100 }}
      />
      <DirectionLight
        // color={0xffffff}
        castShadow={false}
        position={{ x: -10, y: 10, z: -100 }}
      />
    </GLTFModel>

    // </>
  )
}

export default ThreeDViewer
