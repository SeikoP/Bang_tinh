import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

/**
 * NotificationBanner — Slide-in banner for header area.
 * Shows bank notifications or system alerts.
 */
Item {
    id: bannerRoot
    Layout.fillWidth: true
    height: visible ? 40 : 0
    visible: bannerText.text !== ""
    clip: true

    property string message: ""
    property string bannerType: "info"  // "bank", "task", "info"

    function show(msg, type) {
        message = msg
        bannerType = type || "info"
        bannerText.text = msg
        slideIn.start()
    }

    function hide() {
        slideOut.start()
    }

    Behavior on height {
        NumberAnimation { duration: Theme.animFast; easing.type: Easing.OutCubic }
    }

    NumberAnimation {
        id: slideIn
        target: bannerContent
        property: "x"
        from: bannerRoot.width; to: 0
        duration: 300
        easing.type: Easing.OutCubic
    }

    NumberAnimation {
        id: slideOut
        target: bannerContent
        property: "x"
        from: 0; to: bannerRoot.width
        duration: Theme.animNormal
        easing.type: Easing.InCubic
        onFinished: bannerText.text = ""
    }

    Rectangle {
        id: bannerContent
        anchors.fill: parent
        radius: Theme.radiusMd
        color: {
            if (bannerType === "bank") return Theme.withAlpha(Theme.primary, 0.1)
            if (bannerType === "task") return Theme.withAlpha(Theme.warningColor, 0.1)
            return Theme.withAlpha(Theme.info, 0.1)
        }
        border.width: 1
        border.color: {
            if (bannerType === "bank") return Theme.withAlpha(Theme.primary, 0.3)
            if (bannerType === "task") return Theme.withAlpha(Theme.warningColor, 0.3)
            return Theme.withAlpha(Theme.info, 0.3)
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            spacing: Theme.spacingSm

            Rectangle {
                width: 6
                height: 6
                radius: 3
                color: {
                    if (bannerType === "bank") return Theme.primary
                    if (bannerType === "task") return Theme.warningColor
                    return Theme.info
                }
            }

            Label {
                id: bannerText
                Layout.fillWidth: true
                font: Theme.typography.labelMedium
                color: Theme.backgroundText
                elide: Text.ElideRight
                maximumLineCount: 1
            }

            Label {
                text: "×"
                font.pixelSize: 14
                font.weight: Font.Medium
                color: Theme.surfaceVariantText
                MouseArea {
                    anchors.fill: parent
                    anchors.margins: -4
                    cursorShape: Qt.PointingHandCursor
                    onClicked: bannerRoot.hide()
                }
            }
        }
    }
}
