# Sora のデータチャネル機能を使ってメッセージを送信するサンプルスクリプト。
#
# コマンドライン引数で指定されたチャネルおよびラベルに、同じくコマンドライン引数で指定されたデータを送信する。
#
# 実行例:
# $ rye run python messaging_sendonly/messaging_sendonly.py --signaling-url ws://localhost:5000/signaling --channel-id sora --label '#foo' --data hello
import argparse
import json
import time

from sora_sdk import Sora


class MessagingSendonly:
    def __init__(self, signaling_url, channel_id, client_id, label, metadata):
        self.sora = Sora()
        self.connection = self.sora.create_connection(
            signaling_url=signaling_url,
            role="sendrecv",
            channel_id=channel_id,
            client_id=client_id,
            metadata=metadata,
            audio=False,
            video=False,
            data_channels=[{"label": label, "direction": "sendonly"}],
            data_channel_signaling=True,
        )

        self.disconnected = False
        self.label = label
        self.is_data_channel_ready = False
        self.connection.on_data_channel = self.on_data_channel
        self.connection.on_disconnect = self.on_disconnect

    def on_disconnect(self, ec, message):
        print(f"Sora から切断されました: message='{message}'")
        self.disconnected = True

    def on_data_channel(self, label):
        if self.label == label:
            self.is_data_channel_ready = True

    def connect(self):
        self.connection.connect()

    def send(self, data):
        # on_data_channel() が呼ばれるまではデータチャネルの準備ができていないので待機
        while not self.is_data_channel_ready and not self.disconnected:
            time.sleep(0.01)

        self.connection.send_data_channel(self.label, data)
        print(f"メッセージを送信しました: label={self.label}, data={data}")

    def disconnect(self):
        self.connection.disconnect()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    # 必須引数
    parser.add_argument("--signaling-url", required=True, help="シグナリング URL")
    parser.add_argument("--channel-id", required=True, help="チャネルID")
    parser.add_argument("--label", required=True, help="送信するデータチャネルのラベル名")
    parser.add_argument("--data", required=True, help="送信するデータ")

    # オプション引数
    parser.add_argument("--client-id", default='',  help="クライアントID")
    parser.add_argument("--metadata", help="メタデータ JSON")
    args = parser.parse_args()

    metadata = None
    if args.metadata:
        metadata = json.loads(args.metadata)

    messaging_sendonly = MessagingSendonly(args.signaling_url,
                                           args.channel_id,
                                           args.client_id,
                                           args.label,
                                           metadata)
    messaging_sendonly.connect()
    messaging_sendonly.send(args.data.encode("utf-8"))
    messaging_sendonly.disconnect()