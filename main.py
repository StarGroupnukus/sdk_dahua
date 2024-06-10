# coding=utf-8

import datetime

from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Callback import fDisConnect, fHaveReConnect
from NetSDK.SDK_Enum import *
from NetSDK.SDK_Struct import *
from dotenv import load_dotenv

from test import send_report, setup_logger

load_dotenv()

callback_face_recognition_num = 0
detect_object_id = 0

logger = setup_logger("main", "logs/main.log")


class CallBackAlarmInfo:
    def __init__(self):
        self.face_time_str = ""
        self.face_sex_str = ""
        self.face_age_str = ""
        self.face_color_str = ""
        self.face_eye_str = ""
        self.face_mouth_str = ""
        self.face_mask_str = ""
        self.face_bread_str = ""

        self.candidate_name_str = ""
        self.candidate_sex_str = ""
        self.candidate_birth_str = ""
        self.candidate_id_str = ""
        self.candidate_library_no_str = ""
        self.candidate_library_name_str = ""
        self.candidate_similarity_str = ""

    def get_recognition_info(self, alarm_info, is_face, is_candidate):
        if is_face:
            self.face_time_str = '{}-{}-{} {}:{}:{}'.format(
                alarm_info.UTC.dwYear, alarm_info.UTC.dwMonth, alarm_info.UTC.dwDay,
                alarm_info.UTC.dwHour, alarm_info.UTC.dwMinute,
                alarm_info.UTC.dwSecond
            )

            if alarm_info.stuFaceData.emSex == int(EM_DEV_EVENT_FACEDETECT_SEX_TYPE.MAN):
                self.face_sex_str = '(Male)'
            elif alarm_info.stuFaceData.emSex == int(EM_DEV_EVENT_FACEDETECT_SEX_TYPE.WOMAN):
                self.face_sex_str = '(Female)'
            else:
                self.face_sex_str = '(Unknown)'

            if alarm_info.stuFaceData.nAge == 0xff:
                self.face_age_str = '(Unknown)'
            else:
                self.face_age_str = str(alarm_info.stuFaceData.nAge)

            self.face_color_str = '(UNKNOWN)'

            if alarm_info.stuFaceData.emEye == int(EM_EYE_STATE_TYPE.OPEN):
                self.face_eye_str = '(OPEN)'
            elif alarm_info.stuFaceData.emEye == int(EM_EYE_STATE_TYPE.CLOSE):
                self.face_eye_str = '(CLOSE)'
            elif alarm_info.stuFaceData.emEye == int(EM_EYE_STATE_TYPE.NODISTI):
                self.face_eye_str = '(NODISTI)'
            else:
                self.face_eye_str = '(UNKNOWN)'

            if alarm_info.stuFaceData.emMouth == int(EM_MOUTH_STATE_TYPE.OPEN):
                self.face_mouth_str = '(OPEN)'
            elif alarm_info.stuFaceData.emMouth == int(EM_EYE_STATE_TYPE.CLOSE):
                self.face_mouth_str = '(CLOSE)'
            elif alarm_info.stuFaceData.emMouth == int(EM_EYE_STATE_TYPE.NODISTI):
                self.face_mouth_str = '(NODISTI)'
            else:
                self.face_mouth_str = '(UNKNOWN)'

            if alarm_info.stuFaceData.emMask == int(EM_MASK_STATE_TYPE.NOMASK):
                self.face_mask_str = '(NOMASK)'
            elif alarm_info.stuFaceData.emMask == int(EM_MASK_STATE_TYPE.WEAR):
                self.face_mask_str = '(WEAR)'
            elif alarm_info.stuFaceData.emMask == int(EM_MASK_STATE_TYPE.NODISTI):
                self.face_mask_str = '(NODISTI)'
            else:
                self.face_mask_str = '(UNKNOWN)'

            if alarm_info.stuFaceData.emBeard == int(EM_BEARD_STATE_TYPE.NOBEARD):
                self.face_bread_str = '(NOBEARD)'
            elif alarm_info.stuFaceData.emBeard == int(EM_BEARD_STATE_TYPE.HAVEBEARD):
                self.face_bread_str = '(HAVEBEARD)'
            elif alarm_info.stuFaceData.emBeard == int(EM_BEARD_STATE_TYPE.NODISTI):
                self.face_bread_str = '(NODISTI)'
            else:
                self.face_bread_str = '(UNKNOWN)'

        if is_candidate:
            candidate_info = CANDIDATE_INFO()
            for index in range(alarm_info.nCandidateNum):
                if candidate_info.bySimilarity < alarm_info.stuCandidates[index].bySimilarity:
                    candidate_info = alarm_info.stuCandidates[index]

            self.candidate_name_str = str(candidate_info.stPersonInfo.szPersonNameEx, 'utf-8')

            if candidate_info.stPersonInfo.bySex == int(EM_DEV_EVENT_FACEDETECT_SEX_TYPE.MAN):
                self.candidate_sex_str = '(Male)'
            elif candidate_info.stPersonInfo.bySex == int(EM_DEV_EVENT_FACEDETECT_SEX_TYPE.WOMAN):
                self.candidate_sex_str = '(Female)'
            else:
                self.candidate_sex_str = '(Unknown)'

            self.candidate_birth_str = '{}-{}-{}'.format(
                candidate_info.stPersonInfo.wYear,
                candidate_info.stPersonInfo.byMonth,
                candidate_info.stPersonInfo.byDay
            )
            self.candidate_id_str = str(candidate_info.stPersonInfo.szID, 'utf-8')
            if candidate_info.stPersonInfo.pszGroupID:
                self.candidate_library_no_str = str(candidate_info.stPersonInfo.pszGroupID, 'utf-8')
            if candidate_info.stPersonInfo.pszGroupName:
                self.candidate_library_name_str = str(candidate_info.stPersonInfo.pszGroupName, 'utf-8')
            self.candidate_similarity_str = str(candidate_info.bySimilarity)
        else:
            self.candidate_similarity_str = '(Stranger)'


@CB_FUNCTYPE(None, C_LLONG, C_DWORD, c_void_p, POINTER(c_ubyte), C_DWORD, C_LDWORD, c_int, c_void_p)
def AnalyzerDataCallBack(lAnalyzerHandle, dwAlarmType, pAlarmInfo, pBuffer, dwBufSize, dwUser, nSequence, reserved):
    global callback_face_recognition_num
    global detect_object_id

    local_path = os.path.abspath('.')
    is_global = False
    is_face = False
    is_candidate = False

    show_info = CallBackAlarmInfo()
    if dwAlarmType == EM_EVENT_IVS_TYPE.FACERECOGNITION:
        callback_face_recognition_num += 1
        alarm_info = cast(pAlarmInfo, POINTER(DEV_EVENT_FACERECOGNITION_INFO)).contents
        if alarm_info.bGlobalScenePic:
            if pBuffer != 0 and dwBufSize > 0:
                if alarm_info.bGlobalScenePic:
                    if alarm_info.stuGlobalScenePicInfo.dwFileLenth > 0:
                        is_global = True
                        Global_buf = pBuffer[
                                     alarm_info.stuGlobalScenePicInfo.dwOffSet: alarm_info.stuGlobalScenePicInfo.dwOffSet + alarm_info.stuGlobalScenePicInfo.dwFileLenth]
                        if not os.path.isdir(os.path.join(local_path, 'Global_Recogn')):
                            os.mkdir(os.path.join(local_path, 'Global_Recogn'))
                        with open('./Global_Recogn/Global_Img' + str(callback_face_recognition_num) + '.jpg',
                                  'wb+') as global_pic:
                            global_pic.write(bytes(Global_buf))
        if alarm_info.stuObject.stPicInfo.dwFileLenth > 0:
            is_face = True
            Face_buf = pBuffer[
                       alarm_info.stuObject.stPicInfo.dwOffSet:alarm_info.stuObject.stPicInfo.dwOffSet + alarm_info.stuObject.stPicInfo.dwFileLenth]
            if not os.path.isdir(os.path.join(local_path, 'Face_Recogn')):
                os.mkdir(os.path.join(local_path, 'Face_Recogn'))
            with open('./Face_Recogn/Face_Img' + str(callback_face_recognition_num) + '.jpg', 'wb+') as face_pic:
                face_pic.write(bytes(Face_buf))
        if alarm_info.nCandidateNum > 0:
            maxSimilarityPersonInfo = CANDIDATE_INFO()
            for index in range(alarm_info.nCandidateNum):
                if maxSimilarityPersonInfo.bySimilarity < alarm_info.stuCandidates[index].bySimilarity:
                    maxSimilarityPersonInfo = alarm_info.stuCandidates[index]
            if maxSimilarityPersonInfo.stPersonInfo.szFacePicInfo[0].dwFileLenth > 0:
                is_candidate = True
                Candidate_buf = pBuffer[maxSimilarityPersonInfo.stPersonInfo.szFacePicInfo[0].dwOffSet:
                                        maxSimilarityPersonInfo.stPersonInfo.szFacePicInfo[0].dwOffSet +
                                        maxSimilarityPersonInfo.stPersonInfo.szFacePicInfo[0].dwFileLenth]
                if not os.path.isdir(os.path.join(local_path, 'Candidate_Recogn')):
                    os.mkdir(os.path.join(local_path, 'Candidate_Recogn'))
                with open('./Candidate_Recogn/Candidate_Img' + str(callback_face_recognition_num) + '.jpg',
                          'wb+') as candidate_pic:
                    candidate_pic.write(bytes(Candidate_buf))

        show_info.get_recognition_info(alarm_info, is_face, is_candidate)
        process_event(dwAlarmType, show_info, callback_face_recognition_num, is_global, is_face, is_candidate)


def process_event(dwAlarmType, show_info, num, is_global, is_face, is_candidate):
    logger.info('face_recognition')
    if is_global:
        logger.info(f"Global picture saved: Global_Recogn/Global_Img{num}.jpg")

    if is_face:
        logger.info(f"Face picture saved: Face_Recogn/Face_Img{num}.jpg")
        logger.info(
            f"Face info: Time: {show_info.face_time_str}, Sex: {show_info.face_sex_str}, Age: {show_info.face_age_str}")

    if is_candidate:
        logger.info(f"Candidate picture saved: Candidate_Recogn/Candidate_Img{num}.jpg")
        logger.info(
            f"Candidate info: Name: {show_info.candidate_name_str}, Sex: {show_info.candidate_sex_str}, Birth: {show_info.candidate_birth_str}, ID: {show_info.candidate_id_str}, Similarity: {show_info.candidate_similarity_str}")
        file_paths = [f'./Face_Recogn/Face_Img{num}.jpg']
        person_id = show_info.candidate_name_str
        score = show_info.candidate_similarity_str
        status = '1' if int(score) > 70 else '0'
        send_report(person_id, file_paths, datetime.datetime.now(), score, status)
    else:
        logger.warning("Candidate info: Stranger")


def main():
    sdk = NetClient()
    m_DisConnectCallBack = fDisConnect(lambda lLoginID, pchDVRIP, nDVRPort, dwUser: print(f"Disconnected: {pchDVRIP}"))
    m_ReConnectCallBack = fHaveReConnect(lambda lLoginID, pchDVRIP, nDVRPort, dwUser: print(f"Reconnected: {pchDVRIP}"))

    sdk.InitEx(m_DisConnectCallBack)
    sdk.SetAutoReconnect(m_ReConnectCallBack)

    ip = os.getenv('IP_ADRESS')
    port = os.getenv('PORT')
    username = os.getenv('LOGIN')
    password = os.getenv('PASSWORD')
    stuInParam = NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY()
    stuInParam.dwSize = sizeof(NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY)
    stuInParam.szIP = ip.encode()
    stuInParam.nPort = port
    stuInParam.szUserName = username.encode()
    stuInParam.szPassword = password.encode()
    stuInParam.emSpecCap = EM_LOGIN_SPAC_CAP_TYPE.TCP
    stuInParam.pCapParam = None

    stuOutParam = NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY()
    stuOutParam.dwSize = sizeof(NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY)

    loginID, device_info, error_msg = sdk.LoginWithHighLevelSecurity(stuInParam, stuOutParam)
    if loginID != 0:
        logger.info("Login successful")
        channel = 0  # Используйте нужный вам канал
        realloadID = sdk.RealLoadPictureEx(loginID, channel, EM_EVENT_IVS_TYPE.ALL, True, AnalyzerDataCallBack)
        if realloadID != 0:
            logger.info("Listening to events")
            try:
                while True:
                    pass  # В бесконечном цикле, чтобы оставаться в рабочем состоянии и слушать события
            except KeyboardInterrupt:
                logger.error("Stopping...")
                sdk.StopLoadPic(realloadID)
        else:
            logger.error(f"Failed to listen to events: {sdk.GetLastErrorMessage()}")
        sdk.Logout(loginID)
    else:
        logger.error(f"Failed to login: {error_msg}")
    sdk.Cleanup()


if __name__ == '__main__':
    while True:
        try:
            logger.info('start main')
            main()
        except Exception as e:
            logger.error(e)
