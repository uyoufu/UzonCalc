const CONTENT_START_MARK = "<!--CONTENT_START_MARK-->";
const CONTENT_END_MARK = "<!--CONTENT_END_MARK-->";
const UPDATE_MESSAGE_TYPE = "uzoncalc:update-content";

interface ContentPatchMessage {
  type: typeof UPDATE_MESSAGE_TYPE;
  contentHtml: string;
}

/** 判断消息是否为正文增量更新消息。 */
function isContentPatchMessage(data: unknown): data is ContentPatchMessage {
  if (!data || typeof data !== "object") {
    return false;
  }

  const message = data as Partial<ContentPatchMessage>;
  return (
    message.type === UPDATE_MESSAGE_TYPE &&
    typeof message.contentHtml === "string"
  );
}

/** 应用正文增量消息，返回是否实际更新了页面。 */
export function applyContentPatchMessage(data: unknown): boolean {
  if (!isContentPatchMessage(data)) {
    return false;
  }

  const contentElement = document.querySelector(".content");
  if (!contentElement) {
    return false;
  }

  // 保留模板正文标记，便于后续增量更新仍能定位正文边界
  contentElement.innerHTML = `${CONTENT_START_MARK}${data.contentHtml}${CONTENT_END_MARK}`;
  return true;
}

/** 监听父窗口传入的正文补丁消息。 */
export function setupContentPatchMessaging(onUpdated: () => void): void {
  window.addEventListener("message", (event) => {
    if (event.source !== window.parent) {
      return;
    }

    if (applyContentPatchMessage(event.data)) {
      onUpdated();
    }
  });
}
