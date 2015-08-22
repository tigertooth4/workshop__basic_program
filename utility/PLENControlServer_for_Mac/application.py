# -*- encoding:utf8 -*-

import sys, socket, serial, serial.tools.list_ports, time
from ctypes import * 
from flask import Flask, Response, json, make_response, request


application = Flask(__name__)


# シリアルの設定
# ==============================================================================
device_name = None
ser = None


# APIの定義
# ==============================================================================
DEVICE_MAP = {
	"left_shoulder_pitch"  : 0,
	"right_shoulder_pitch" : 12,
	"left_shoulder_roll"   : 2,
	"right_shoulder_roll"  : 14,
	"left_elbow_roll"      : 3,
	"right_elbow_roll"     : 15,
	"left_thigh_yaw"       : 1,
	"right_thigh_yaw"      : 13,
	"left_thigh_roll"      : 4,
	"right_thigh_roll"     : 16,
	"left_thigh_pitch"     : 5,
	"right_thigh_pitch"    : 17,
	"left_knee_pitch"      : 6,
	"right_knee_pitch"     : 18,
	"left_foot_pitch"      : 7,
	"right_foot_pitch"     : 19,
	"left_foot_roll"       : 8,
	"right_foot_roll"      : 20
}

VALUE_MAP = [
	None,
	None,
	None,
	None,
	None,
	None,
	None,
	None,
	None,
	900,
	900,
	900,
	None,
	None,
	None,
	None,
	None,
	None,
	None,
	None,
	None,
	900,
	900,
	900
]

CWC_MAP = [
	1,
	1,
	1,
	-1, # 左肘ロール
	1,
	1,
	1,
	1,
	1,
	1,
	1,
	1,
	1,
	1,
	1,
	-1, # 右肘ロール
	1,
	1,
	1,
	1,
	-1, # 右足ロール
	1,
	1,
	1
]


def jointMove(id, angle):
	global ser
	if ser == None:
		return False

	cmd = "#SD%02x%04x" % (id, c_ushort(angle).value)
	ser.write(cmd)

	return True


def installMotion(json_data):
	global ser
	if ser == None:
		return False

	# コマンドの指定
	cmd = "#IN"
	# スロット番号の指定
	cmd += "%02x" % (json_data["slot"])
	# モーション名の指定
	if len(json_data["name"]) < 20:
		cmd += json_data["name"].ljust(20)
	else:
		cmd += json_data["name"][:19]
	# 制御機能の指定
	cmd += "000000"
	# フレーム数の指定
	cmd += "%02x" % (len(json_data["frames"]))
	# フレーム構成要素の指定
	for frame in json_data["frames"]:
		# 遷移時間の指定
		cmd += "%04x" % (frame["transition_time_ms"])

		for output in frame["outputs"]:
			VALUE_MAP[DEVICE_MAP[output["device"]]] = c_ushort(output["value"] * CWC_MAP[DEVICE_MAP[output["device"]]]).value
			# cmd += "%02x" % (DEVICE_MAP[output["device"]])
			# cmd += "%04x" % (c_ushort(output["value"]).value)

		for val in VALUE_MAP:
			cmd += "%04x" % val

	ser.write(cmd.encode())

	return True


def playMotion(slot):
	global ser
	if ser == None:
		return False

	cmd = "$MP" + "%02x" % slot
	ser.write(cmd)

	return True


def BLEConnect():
	global device_name
	if device_name == None:
		return False

	global ser
	if ser == None:
		ser = serial.Serial(port = device_name, baudrate = 2000000, timeout = 1)
		ser.flushInput()
		ser.flushOutput()

	return True


def BLEDisconnect():
	global ser
	if ser == None:
		return False

	ser.close()
	ser = None

	return True


# WEB APIの定義
# ==============================================================================
def jsonp(data, callback = "function"):
	return Response(
		"%s(%s)" % (callback, json.dumps(data)),
		mimetype = "text/javascript"
	)


# REST API for "jointMove command".
# ==============================================================================
@application.route("/jointmove/<ID>/<ANGLE>/")
def jointmove(ID, ANGLE):
	data = {
		"command" : "Joint Move",
		"ID"      : ID,
		"ANGLE"   : ANGLE,
		"result"  : None
	}
	callback = request.args.get("callback")
	
	data["result"] = jointMove(DEVICE_MAP[ID], int(ANGLE))

	if callback:
		return jsonp(data, callback)
	
	return jsonp(data)


# REST API for "playMotion command".
# ==============================================================================
@application.route("/play/<SLOT>/")
def play(SLOT):
	data = {
		"command" : "Play Motion",
		"SLOT"    : SLOT,
		"result"  : None
	}
	callback = request.args.get("callback")
	
	data["result"] = playMotion(int(SLOT))

	if callback:
		return jsonp(data, callback)
	
	return jsonp(data)


# REST API for "install command".
# ==============================================================================
@application.route("/install/", methods = ["OPTIONS"])
def return_xhr2_response_header__install():
	response = make_response()
	response.headers['Access-Control-Allow-Origin']  = '*'
	response.headers["Access-Control-Allow-Headers"] = "Origin, X-Requested-With, Content-Type, Accept"

	return response

@application.route("/install/", methods = ["POST"])
def install():
	data = {
		"command" : "Install",
		"result"  : None
	}

	data["result"] = installMotion(request.json)

	response = make_response(json.dumps(data, sort_keys = True, indent = 4))
	response.headers["Access-Control-Allow-Origin"] = "*"
	response.mimetype = "application/json"

	return response


# REST API for "connect command".
# ==============================================================================
@application.route("/connect/")
def connect():
	data = {
		"command" : "BLE Connect",
		"result"  : None
	}
	callback = request.args.get("callback")
	
	data["result"] = BLEConnect()

	if callback:
		return jsonp(data, callback)
	
	return jsonp(data)


# REST API for "disconnect command".
# ==============================================================================
@application.route("/disconnect/")
def disconnect():
	data = {
		"command" : "BLE Disconnect",
		"result"  : None
	}
	callback = request.args.get("callback")

	data["result"] = BLEDisconnect()

	if callback:
		return jsonp(data, callback)

	return jsonp(data)


# アプリケーション・エントリポイント
# ==============================================================================
def main():
	print '==============================================================================='
	print 'usage : ControlServer.exe <port no.> <MAC addr.>'
	print "<device name> : required, please set your PLEN's device name."
	print '<port no.>    : additional, default value is "17264".'
	print '==============================================================================='

	global device_name
	if len(sys.argv) < 2:
		print "Error! : Please set <device name>."
		print '==============================================================================='

		sys.exit()
	else:
		device_name = sys.argv[1]

	arg_port = None
	if len(sys.argv) > 2:
		arg_port = int(sys.argv[2])
	else:
		arg_port = 17264

	ip = socket.gethostbyname(socket.gethostname())
	print '"PLEN Control Server" is on "%s:%d".' % (ip, arg_port)
	print 'Connect to "%s".' % (device_name)
	print '==============================================================================='

	application.debug = False
	application.run(host = "0.0.0.0", port = arg_port)


if __name__ == "__main__":
	main()