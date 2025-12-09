import React, { useEffect, useState, useContext } from "react"
import { Canvas } from "@react-three/fiber"
import { OrbitControls, Html, Bounds } from "@react-three/drei"
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader"
import type { Group } from "three"
import { getNewUrl } from "../../utils/http"
import { suuidContext } from "../../components/ConText"

interface ThreeDViewerProps {
  modelUrl: any
}

export interface ScaleProps {
  x: number
  y: number
  z: number
}

/**
 * ModelSafe: 以二进制方式 fetch 模型，验证 header 与 magic bytes，
 * 仅当确认是合法 GLB（glTF 2.0 binary）时才 parse 并渲染。
 */
const ModelSafe: React.FC<{
  url: string
  scale?: ScaleProps
}> = ({ url, scale = { x: 1, y: 1, z: 1 } }) => {
  const [object, setObject] = useState<Group | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setObject(null)
    setError(null)
    setLoading(true)

    const loader = new GLTFLoader()

    ;(async () => {
      try {
        const res = await fetch(url, { method: "GET" })

        if (!res.ok) {
          const txt = await res.text().catch(() => "")
          throw new Error(`HTTP ${res.status} ${res.statusText}: ${txt.substring(0, 200)}`)
        }

        const contentType = (res.headers.get("content-type") || "").toLowerCase()

        // 若明显是文本/JSON/HTML，直接抛错（说明后端并未返回二进制 glb）
        if (contentType.startsWith("application/json") || contentType.startsWith("text/") || contentType.includes("html")) {
          const txt = await res.text().catch(() => "")
          throw new Error(`Response is not binary GLB. content-type=${contentType}, body=${txt.substring(0, 500)}`)
        }

        const arrayBuffer = await res.arrayBuffer()

        // 检查 GLB magic header: 前4字节为 ASCII "glTF"
        const header = new Uint8Array(arrayBuffer, 0, 4)
        const headerStr = String.fromCharCode(header[0], header[1], header[2], header[3])
        if (headerStr !== "glTF") {
          throw new Error("Invalid GLB header (not glTF 2.0 binary). header=" + headerStr)
        }

        // 解析 GLB（二进制）
        loader.parse(
          arrayBuffer,
          "", // path
          (gltf) => {
            if (cancelled) return
            setObject(gltf.scene as unknown as Group)
            setLoading(false)
          },
          (err) => {
            if (cancelled) return
            const msg = "GLTF parse error: " + (err?.message || String(err))
            setError(msg)
            setLoading(false)
            console.error(msg)
          }
        )
      } catch (e: any) {
        if (cancelled) return
        const msg = e?.message ? String(e.message) : String(e)
        setError(msg)
        setLoading(false)
        console.warn("ModelSafe load error:", msg, url)
      }
    })()

    return () => {
      cancelled = true
    }
  }, [url])

  if (loading) {
    return <Html center>Loading...</Html>
  }

  if (error || !object) {
    return null
  }

  return (
    <Bounds fit clip margin={1.5}>
      <primitive object={object} scale={[scale.x, scale.y, scale.z]} />
    </Bounds>
  )
}

const ThreeDViewer: React.FC<ThreeDViewerProps> = ({ modelUrl }) => {
  const conText = useContext(suuidContext)
  const newModelUrl = getNewUrl(modelUrl, conText)

  return (
    <div style={{ width: "800px", height: "800px" }} onWheel={(e) => e.stopPropagation()}>
      <Canvas style={{ width: "100%", height: "100%" }} camera={{ position: [0, 0, 5], fov: 45 }}>
        <ambientLight color={0xffffff} />
        <directionalLight position={[10, 10, 100]} castShadow={false} />
        <directionalLight position={[-10, -10, 100]} castShadow={false} />
        <directionalLight position={[10, -10, 100]} castShadow={false} />
        <directionalLight position={[-10, 10, 100]} castShadow={false} />
        <directionalLight position={[10, 10, -100]} castShadow={false} />
        <directionalLight position={[-10, -10, -100]} castShadow={false} />
        <directionalLight position={[10, -10, -100]} castShadow={false} />
        <directionalLight position={[-10, 10, -100]} castShadow={false} />

        <ModelSafe url={newModelUrl} scale={{ x: 1, y: 1, z: 1 }} />

        <OrbitControls enableZoom={true} />
      </Canvas>
    </div>
  )
}

export default ThreeDViewer
