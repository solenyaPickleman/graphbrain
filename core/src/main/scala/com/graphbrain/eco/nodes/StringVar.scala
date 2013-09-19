package com.graphbrain.eco.nodes

import com.graphbrain.eco.{Contexts, Context, NodeType}

class StringVar(name: String, val value: String) extends VarNode(name) {
  override def ntype = NodeType.String
  override def stringValue(ctxts: Contexts, ctxt: Context) = value

  override def equals(obj:Any) = obj match {
    case s: StringVar => s.name == name
    case _ => false
  }
}