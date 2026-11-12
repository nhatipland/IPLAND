// Chuyển tin zca-js -> định dạng CareAI. Hàm thuần để test. Không giữ nội dung file/ảnh/ghi âm (chỉ loại).
export function normalize(msg, ownId, groupType = 1) {
  if (msg.type !== groupType) return null;           // chỉ nhóm
  const d = msg.data;
  const isText = typeof d.content === "string";
  const mt = String(d.msgType || "");
  const kind = isText ? "text" : /voice/.test(mt) ? "voice" : /photo|image/.test(mt) ? "image" : "file";
  return {
    group_ext_id: String(msg.threadId),
    msg_ext_id: String(d.msgId),
    sender_ext_id: String(d.uidFrom),
    sender_name: String(d.dName || ""),
    ts: Number(d.ts) / 1000,
    text: isText ? d.content : "",
    kind,
    // CHƯA kiểm chứng: quote.globalMsgId có khớp msgId của tin gốc hay không
    reply_to_ext_id: d.quote?.globalMsgId != null ? String(d.quote.globalMsgId) : null,
    mentions: (d.mentions || []).map((x) => String(x.uid)),
    is_self: Boolean(msg.isSelf) || String(d.uidFrom) === String(ownId),
  };
}
