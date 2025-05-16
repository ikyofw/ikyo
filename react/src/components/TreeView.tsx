import { TreeItem, TreeView } from "@material-ui/lab"
import { Checkbox } from "@mui/material"
import { Button, Input, Space } from "antd"
import React, { useRef, useState, forwardRef, Ref, useImperativeHandle } from "react"
import pyiLocalStorage from "../utils/pyiLocalStorage"

const globalParam = pyiLocalStorage.globalParams
const folderIcon = globalParam.PUBLIC_URL + "images/icon_park_right.png"
const folderOpenIcon = globalParam.PUBLIC_URL + "images/icon_park_down.png"
const pageIcon = globalParam.PUBLIC_URL + "images/page.gif"

interface TreeNode {
  id: any
  title: string
  icon?: string
  subMenus?: TreeNode[]
  parentId?: any
}

interface ITree {
  ref: any
  selectable: boolean
  data: TreeNode[]
  initNodeIDs?: string[]
  // onSelectedNodesChange?: (selectedNodes: string[]) => void
  // onNodeClick?: (node: TreeNode) => void
  onFilteredDataChange?: (filteredData: TreeNode[]) => void
}

const filterTree = (nodes: TreeNode[], searchTerm: string, selectedNodes: string[], hideUnselected: boolean): TreeNode[] => {
  const lowerCasedTerm = searchTerm.toLowerCase()

  const filterNode = (node: TreeNode): boolean => {
    let hasMatchingSubNode = false
    if (node.subMenus) {
      // Recursively check if any sub-node matches the search term
      hasMatchingSubNode = node.subMenus.some((subNode) => filterNode(subNode))
    }

    if (hasMatchingSubNode) {
      return true
    }

    // Show node if it or any of its sub-nodes matches the search term
    if (!hideUnselected && lowerCasedTerm && node.title.toLowerCase().includes(lowerCasedTerm)) {
      return true
    } else if (!hideUnselected && lowerCasedTerm) {
      return false
    }

    // Additionally, if hiding unselected nodes, ensure that the node is selected
    if (hideUnselected && selectedNodes.includes(node.id)) {
      return true
    } else if (!hideUnselected) {
      return true
    }

    return false
  }

  const filterNodes = (nodes: TreeNode[]): TreeNode[] =>
    nodes
      .filter((node) => {
        return filterNode(node)
      })
      .map((node) => ({
        ...node,
        // If the node matches the search term, don't filter its sub-nodes
        subMenus: lowerCasedTerm && node.title.toLowerCase().includes(lowerCasedTerm) ? node.subMenus : filterNodes(node.subMenus || []),
      }))

  return filterNodes(nodes)
}

const findPath = (TreeNodes: TreeNode[], targetNode: string) => {
  let path = []

  function dfs(node, currentPath) {
    if (!node) {
      return false
    }
    currentPath.push(node.id)
    if (node.id === targetNode) {
      path = [...currentPath]
      return true
    }
    if (node.subMenus) {
      for (let subMenus of node.subMenus) {
        if (dfs(subMenus, currentPath)) {
          return true
        }
      }
    }
    currentPath.pop()
    return false
  }

  TreeNodes.forEach((TreeNode) => {
    dfs(TreeNode, [])
  })
  return path
}

const getAllNodeIds = (nodes: TreeNode[]): string[] => {
  let ids: string[] = []
  const traverse = (node: TreeNode) => {
    ids.push(node.id.toString())
    if (node.subMenus) {
      node.subMenus.forEach((subNode) => traverse(subNode))
    }
  }
  nodes.forEach((node) => traverse(node))
  return ids
}

const getLevel2NodeIds = (nodes: TreeNode[]): string[] => {
  let ids: string[] = []
  const traverse = (node: TreeNode, level: number) => {
    if (level <= 1) {
      ids.push(node.id.toString())
    }
    if (node.subMenus) {
      node.subMenus.forEach((subNode) => traverse(subNode, level + 1))
    }
  }
  nodes.forEach((node) => traverse(node, 1))
  return ids
}

const RecursiveTreeItem: React.FC<{
  node: TreeNode
  selectedNodes: string[]
  expandedNodes: string[]
  handleToggle?: (node: TreeNode) => void
  handleExpand: (node: TreeNode) => void
}> = React.memo(
  ({ node, selectedNodes, expandedNodes, handleToggle, handleExpand }) => {
    return (
      <TreeItem
        nodeId={node.id.toString()}
        label={
          <div style={{ display: "flex", alignItems: "center" }}>
            {handleToggle && (
              <Checkbox
                checked={selectedNodes.includes(node.id)}
                onClick={(event) => {
                  event.stopPropagation()
                  handleToggle(node)
                }}
                style={{ padding: 0, transform: "scale(0.8)" }}
              />
            )}
            <div style={{ marginLeft: "4px" }}>{node.title}</div>
          </div>
        }
        onIconClick={() => handleExpand(node)}
        onLabelClick={() => handleExpand(node)}
        icon={node.icon && <img src={node.icon} alt="node icon" />}
      >
        {Array.isArray(node.subMenus)
          ? node.subMenus.map((subNode) => (
              <RecursiveTreeItem
                key={subNode.id}
                node={subNode}
                selectedNodes={selectedNodes}
                expandedNodes={expandedNodes}
                handleToggle={handleToggle}
                handleExpand={handleExpand}
              />
            ))
          : null}
      </TreeItem>
    )
  },
  (prevProps, nextProps) => {
    return (
      prevProps.selectedNodes === nextProps.selectedNodes && prevProps.expandedNodes === nextProps.expandedNodes && prevProps.node === nextProps.node
    )
  }
)

const Tree: React.FC<ITree> = forwardRef(({ selectable, data, initNodeIDs, onFilteredDataChange }, ref: Ref<any>) => {
  useImperativeHandle(ref, () => {
    // send data to parent component
    return {
      data: selectedNodes,
    }
  })

  const spaceRef = useRef(null)
  const [treeMaxHeight, setTreeMaxHeight] = useState<string>("")

  const [selectedNodes, setSelectedNodes] = useState<string[]>([])
  const [expandedNodes, setExpandedNodes] = useState<string[]>([])
  const [searchTerm, setSearchTerm] = useState("")
  const [hideUnselected, setHideUnselected] = useState(false)
  const [filteredData, setFilteredData] = useState<TreeNode[]>([])

  React.useEffect(() => {
    if (spaceRef.current) {
      const height = "calc(100vh - 50px - 40px - 20px - " + spaceRef.current.offsetHeight + "px)"
      // 50px: topBar height
      // 40px: Left Panel padding*2
      // 20px: Tree padding*2
      setTreeMaxHeight(height)
    }
  }, [])

  React.useEffect(() => {
    if (onFilteredDataChange) {
      onFilteredDataChange(filteredData)
    }
  }, [filteredData])

  React.useEffect(() => {
    const filteredData = filterTree(data, searchTerm, selectedNodes, hideUnselected)
    setFilteredData(filteredData)

    if (initNodeIDs && filteredData.length > 0 && expandedNodes.length === 0) {
      let defaultExpandedNodes = []
      initNodeIDs.forEach((selectedNodeID) => {
        const path = findPath(filteredData, selectedNodeID)
        path.forEach((nodeId) => {
          if (!defaultExpandedNodes.includes(String(nodeId))) {
            defaultExpandedNodes.push(String(nodeId))
          }
        })
      })
      setExpandedNodes(defaultExpandedNodes)
    }
  }, [data, searchTerm, selectedNodes, hideUnselected])
  React.useEffect(() => {
    if (initNodeIDs && initNodeIDs.length > 0) {
      setSelectedNodes(initNodeIDs)
    }
  }, [initNodeIDs])

  const handleToggle = (node: TreeNode) => {
    if (!selectable) return

    const toggleNode = (node: TreeNode, selected: boolean, selectedNodes: string[]): string[] => {
      const isSelected = selectedNodes.includes(node.id)
      let newSelectedNodes = selected
        ? !isSelected
          ? [...selectedNodes, node.id]
          : selectedNodes
        : isSelected
        ? selectedNodes.filter((id) => id !== node.id)
        : selectedNodes

      if (node.subMenus) {
        node.subMenus.forEach((subNode) => {
          newSelectedNodes = toggleNode(subNode, selected, newSelectedNodes)
        })
      }

      return newSelectedNodes
    }

    const isSelected = selectedNodes.includes(node.id)
    const finalSelectedNodes = toggleNode(node, !isSelected, selectedNodes)
    // onSelectedNodesChange(finalSelectedNodes)
    setSelectedNodes(finalSelectedNodes)
  }

  const handleExpand = (node: TreeNode) => {
    if (!node.subMenus || node.subMenus.length === 0) {
      handleToggle(node)
    }

    const nodeId = node.id.toString()
    setExpandedNodes((prev) => (prev.includes(nodeId) ? prev.filter((id) => id !== nodeId) : [...prev, nodeId]))
    if (!selectable) {
      setSelectedNodes([node.id])
    }
  }
  const handleExpandAll = () => {
    setExpandedNodes(getAllNodeIds(data))
  }
  const handleToggleLevel2 = () => {
    setExpandedNodes(getLevel2NodeIds(data))
  }
  const handleCollapseAll = () => {
    setExpandedNodes([])
  }
  const handleHideUnselected = () => {
    setHideUnselected((prev) => !prev)
  }

  const ITreeNode = React.useMemo(() => {
    return (
      <div className="tree-container">
        <div className="fixed-header">
          <Space ref={spaceRef} direction="vertical" size={5} className="search-buttons">
            <div>
              <Input placeholder="Search..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value.toUpperCase())} />
            </div>
            <div>
              <Button onClick={handleExpandAll} title="Expand All">
                +
              </Button>
              <Button onClick={handleCollapseAll} title="Collapse All">
                -
              </Button>
              <Button onClick={handleToggleLevel2} title="Toggle to Level 2">
                + +
              </Button>
              {selectable ? (
                <Button
                  onClick={handleHideUnselected}
                  style={hideUnselected ? { backgroundColor: "#CCCCFF" } : null}
                  title={hideUnselected ? "Show All" : "Hide Unselected"}
                >
                  - -
                </Button>
              ) : null}
            </div>
          </Space>
        </div>
        <div className="scroll-content" style={{ maxHeight: treeMaxHeight }}>
          <TreeView
            defaultCollapseIcon={<img src={folderOpenIcon} alt="folder open icon" />}
            defaultExpandIcon={<img src={folderIcon} alt="folder icon" />}
            defaultEndIcon={<img src={pageIcon} alt="base icon" />}
            expanded={expandedNodes}
          >
            {filteredData.map((node) => (
              <RecursiveTreeItem
                key={node.id}
                node={node}
                selectedNodes={selectedNodes}
                expandedNodes={expandedNodes}
                handleToggle={selectable ? handleToggle : undefined}
                handleExpand={handleExpand}
              />
            ))}
          </TreeView>
        </div>
      </div>
    )
  }, [filteredData, expandedNodes, selectedNodes])

  return <>{ITreeNode}</>
})

export default Tree
