"""表格存储的基本入门代码"""
"""初始化tablestore sdk对象"""
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
# from tablestore import OTSClient,TableMeta,TableOptions,ReservedThroughput,CapacityUnit,PK_AUTO_INCR
from tablestore import *


class OTS(object):
    def __init__(self):
        self.client = OTSClient(settings.OTS_ENDPOINT, settings.OTS_ID, settings.OTS_SECRET, settings.OTS_INSTANCE)

    def list_table(self):
        """列出所有的存储表"""
        return self.client.list_table()

    def create_table(self, table_name, schema_of_primary_key):
        """
        :param table_name: 字符串，表名
        :param schema_of_primary_key: 列表，每一个成员是一个元祖，表示字段的名称和类型
        :return:
        """
        # 通过表名和主键列的schema创建一个tableMeta。
        table_meta = TableMeta(table_name, schema_of_primary_key)
        # 创建TableOptions，数据保留31536000秒，超过后自动删除；最大3个版本；写入时指定的版本值和当前标准时间相差不能超过1天。
        table_options = TableOptions(31536000, 3, 86400)
        # 设置预留读吞吐量为0，预留写吞吐量为0。
        reserved_throughput = ReservedThroughput(CapacityUnit(0, 0))

        try:
            self.client.create_table(table_meta, table_options, reserved_throughput)
            return True
        # 处理异常。
        except Exception:
            return False

    def delete_table(self, table_name):
        """
        删除表
        :param table_name: 参数如果是字符串，则表示删除一张表，
                           参数如果是列表，则表示删除多张表
        :return:
        """
        tables = []
        if type(table_name) is str:
            tables.append(table_name)
        else:
            tables = table_name

        ret = {
            "success": [],
            "fails": []
        }
        for table in tables:
            try:
                self.client.delete_table(table)
                ret["success"].append(table)
            except Exception:
                ret["fails"].append(table)

        return ret

    def put_row(self, table_name, primary_key, attribute_columns={}):
        """
        添加一条数据
        :param table_name: 本次添加数据的表名
        :param primary_key: 主键列
        :param attribute_columns: 其他属性列
        :return: 新增数据的主键
        """

        primary_key_list = []
        for key, value in primary_key.items():
            primary_key_list.append((key, value))

        attribute_columns_list = []
        for key, value in attribute_columns.items():
            attribute_columns_list.append((key, value))

        row = Row(primary_key_list, attribute_columns_list)
        # 添加数据的条件
        # EXPECT_NOT_EXIST 如果主键重复，则报错！
        condition = Condition(RowExistenceExpectation.EXPECT_NOT_EXIST)
        try:
            # 调用put_row方法, ReturnType.RT_PK表示返回新增数据的主键信息，如果不设置则返回None
            consumed, return_row = self.client.put_row(table_name, row, condition, ReturnType.RT_PK)
            return True, return_row.primary_key
        except OTSClientError as e:
            """网络异常"""
            return False, "put row failed, http_status:%d, error_message:%s" % (
                e.get_http_status(), e.get_error_message())

        # 服务端异常，一般为参数错误或者流控错误。
        except OTSServiceError as e:
            """参数有误"""
            return False, "put row failed, http_status:%d, error_code:%s, error_message:%s, request_id:%s" % (
                e.get_http_status(), e.get_error_code(), e.get_error_message(), e.get_request_id())
        except Exception as e:
            """其他错误"""
            return False, "未知的异常"

    def get_row(self, table_name, primary_key, columns_to_get=[], column_filter=None):
        """"""
        # 指定查询结果返回的属性列
        # 过滤条件
        """
        # ====================== 多条件 ========================
        # 逻辑条件
        cond = CompositeColumnCondition(LogicalOperator.AND)
        cond = CompositeColumnCondition(LogicalOperator.OR)
        cond = CompositeColumnCondition(LogicalOperator.NOT)
        # 比较条件
        ComparatorType.NOT_EQUAL  !=
        ComparatorType.EQUAL      ==
        GREATER_THAN              >
        GREATER_EQUAL             >=
        LESS_THAN                 <
        LESS_EQUAL                <=
        举例：
          查询一个学生信息，性别为男的，小于20岁===>   (sex=男 and age < 20) or (sex=女 and age < 17) 
            cond = CompositeColumnCondition(LogicalOperator.AND)
            cond.add_sub_condition(SingleColumnCondition("sex", '男', ComparatorType.EQUAL))
            cond.add_sub_condition(SingleColumnCondition("age", 20, ComparatorType.LESS_THAN))

        # ====================== 单条件 ======================== 
        cond = SingleColumnCondition("age", 20, ComparatorType.LESS_THAN)
        """
        primary_key_list = []
        for key, value in primary_key.items():
            primary_key_list.append((key, value))
        try:
            # 调用get_row接口查询
            consumed, return_row, next_token = self.client.get_row(table_name, primary_key_list, columns_to_get,
                                                                   column_filter, 1)
            data = {}
            for att in return_row.primary_key:
                # 打印每一个字段的内容
                data[att[0]] = att[1]
            if len(columns_to_get) > 0:
                """如果有指定要返回其他属性列"""
                for att in return_row.attribute_columns:
                    # 打印每一个字段的内容
                    data[att[0]] = att[1]
            return True, data
            # 客户端异常，一般为参数错误或者网络异常。
        except OTSClientError as e:
            return False, "获取数据失败, http_status:%d, error_message:%s" % (e.get_http_status(), e.get_error_message())
        # 服务端异常，一般为参数错误或者流控错误。
        except OTSServiceError as e:
            return False, "获取数据失败, http_status:%d, error_code:%s, error_message:%s, request_id:%s" % (
                e.get_http_status(), e.get_error_code(), e.get_error_message(), e.get_request_id())
        except Exception as e:
            return False, "未知异常"

    def update_row(self, table_name, primary_key, attribute_columns):
        """更新一条数据"""
        primary_key_list = []
        for key, value in primary_key.items():
            primary_key_list.append((key, value))

        attribute_columns_list = []
        for key, value in attribute_columns.items():
            attribute_columns_list.append((key, value))

        update_of_attribute_columns = {
            'PUT': attribute_columns_list,
        }

        row = Row(primary_key_list, update_of_attribute_columns)

        try:
            consumed, return_row = self.client.update_row(table_name, row, condition=None, return_type=ReturnType.RT_PK)
            data = {}
            for att in return_row.primary_key:
                # 打印每一个字段的内容
                data[att[0]] = att[1]

            return True, data
        # 客户端异常，一般为参数错误或者网络异常。
        except OTSClientError as e:
            return False, "更新失败, http_status:%d, error_message:%s" % (e.get_http_status(), e.get_error_message())

        # 服务端异常，一般为参数错误或者流控错误。
        except OTSServiceError as e:
            return False, "更新失败, http_status:%d, error_code:%s, error_message:%s, request_id:%s" % (
                e.get_http_status(), e.get_error_code(), e.get_error_message(), e.get_request_id())
        except Exception as e:
            return False, "未知异常"

    def delete_row(self, table_name, primary_key):
        """根据主键删除一条数据"""
        primary_key_list = []
        for key, value in primary_key.items():
            primary_key_list.append((key, value))
        row = Row(primary_key_list)
        try:
            consumed, return_row = self.client.delete_row(table_name, row, None)
            return True, "删除成功"
        except OTSClientError as e:
            return False, "更新失败！网络异常, http_status:%d, error_message:%s" % (e.get_http_status(), e.get_error_message())
        except OTSServiceError as e:
            return False, "更新失败，参数有误, http_status:%d, error_code:%s, error_message:%s, request_id:%s" % (
                e.get_http_status(), e.get_error_code(), e.get_error_message(), e.get_request_id())
        except Exception as e:
            return False, "未知异常"

    def get_list_0(self, table_name, primary_key_list, columns_to_get=[], column_filter=None):
        """
        根据指定主键查询多条数据
        :param table: 字符串，表名
        :param primary_key_list: 主键列表
        :param columns_to_get: 返回属性字段列表
        :param column_filter: 条件
        :return: 列表， 查询结果
        """

        # 读取3行。
        rows_to_get = []
        for item in primary_key_list:
            primary_key = []
            for key, value in item.items():
                primary_key.append((key, value))
            rows_to_get.append(primary_key)

        # 构造批量读请求。
        request = BatchGetRowRequest()

        # 增加表table_name中需要读取的行，最后一个参数1表示读取最新的一个版本。
        request.add(TableInBatchGetRowItem(table_name, rows_to_get, columns_to_get, column_filter, 1))

        try:
            result = self.client.batch_get_row(request)
            if result.is_all_succeed():
                """只有在获取到全部数据以后才表示读取多条数据成功"""
                table_result = result.get_result_by_table(table_name)
                data = []
                for item in table_result:
                    row = {}

                    if item.is_ok:
                        for att in item.row.primary_key:
                            # 打印每一个字段的内容
                            row[att[0]] = att[1]

                        for att in item.row.attribute_columns:
                            # 打印每一个字段的内容
                            row[att[0]] = att[1]

                    else:
                        return False, '部分数据参数有误，读取数据失败。 error code: %s, error message: %s' % (
                            item.error_code, item.error_message)

                    data.append(row)

                return True, data

            else:
                return False, '部分数据参数有误，读取数据失败。'

        # 客户端异常，一般为参数错误或者网络异常。
        except OTSClientError as e:
            return False, "读取数据失败，网络异常。 http_status:%d, error_message:%s" % (e.get_http_status(), e.get_error_message())
        # 服务端异常，一般为参数错误或者流控错误。
        except OTSServiceError as e:
            return False, "读取数据失败，参数有误。 http_status:%d, error_code:%s, error_message:%s, request_id:%s" % (
                e.get_http_status(), e.get_error_code(), e.get_error_message(), e.get_request_id())
        except Exception as e:
            return False, "未知异常"

    def add_list(self, table_name, primary_key_list, attribute_columns_list=[]):
        """
        添加多条数据
        :param table_name: 字符串，表名
        :param primary_key_list: 主键列
        :param attribute_columns_list: 属性列
        :return:
        """
        put_row_items = self.row_items(PutRowItem, primary_key_list, attribute_columns_list)
        status, result = self.request(table_name, put_row_items)
        if status == False:
            return False, result
        # 输出每一行添加数据的结果。
        succ, fail = result.get_put()
        for item in succ:
            print('添加数据成功, consume %s write cu.' % item.consumed.write)
        for item in fail:
            print('添加数据失败, error code: %s, error message: %s' % (item.error_code, item.error_message))

        return True

    def update_list(self, table_name, primary_key_list, attribute_columns_list=[]):
        """更新多条数据"""
        update_row_items = self.row_items(UpdateRowItem, primary_key_list, attribute_columns_list)
        status, result = self.request(table_name, update_row_items)
        if status == False:
            return False, result

        # 输出每一行更新数据的结果
        succ, fail = result.get_update()
        for item in succ:
            print('更新数据成功, consume %s write cu.' % item.consumed.write)
        for item in fail:
            print('更新数据失败, error code: %s, error message: %s' % (item.error_code, item.error_message))

        return True

    def delete_list(self, table_name, primary_key_list):
        """删除多条数据"""
        delete_row_items = self.row_items(DeleteRowItem, primary_key_list)
        status, result = self.request(table_name, delete_row_items)
        if status == False:
            return False, result
        # 输出每一行删除数据的结果。
        succ, fail = result.get_delete()
        for item in succ:
            print('删除数据成功, consume %s write cu.' % item.consumed.write)
        for item in fail:
            print('删除数据失败, error code: %s, error message: %s' % (item.error_code, item.error_message))

        return True

    def row_items(self, cls, primary_key_list, attribute_columns_list=[]):

        if len(primary_key_list) != len(attribute_columns_list) and len(attribute_columns_list) != 0:
            return False, "参数有误！主键和属性列数量不对应，无法完成添加操作"

        # 增加多行组件的组装。
        row_items = []
        for key0, primary_item in enumerate(primary_key_list):
            primary_row = []
            for key1, value in primary_item.items():
                primary_row.append((key1, value))

            attribute_row = None
            if len(attribute_columns_list) > 0:
                if cls == PutRowItem:
                    """添加多条"""
                    attribute_row = []
                    for key2, value in attribute_columns_list[key0].items():
                        attribute_row.append((key2, value))
                elif cls == UpdateRowItem:
                    """更新多条"""
                    attribute_row = {"put": []}
                    for key2, value in attribute_columns_list[key0].items():
                        attribute_row["put"].append((key2, value))

            row = Row(primary_row, attribute_row)
            condition = Condition(RowExistenceExpectation.IGNORE)
            item = cls(row, condition)
            row_items.append(item)

        return row_items

    def request(self, table_name, put_row_items):
        """
        构造批量写请求
        :param table_name:
        :param put_row_items:
        :return:
        """
        request = BatchWriteRowRequest()
        request.add(TableInBatchWriteRowItem(table_name, put_row_items))
        try:
            result = self.client.batch_write_row(request)
            if result.is_all_succeed():
                return True, result

        except OTSClientError as e:
            print(e.get_http_status(), e.get_error_message())
            return False, "网络异常, http_status:%d, error_message:%s" % (e.get_http_status(), e.get_error_message())
        except OTSServiceError as e:
            return False, "参数有误, http_status:%d, error_code:%s, error_message:%s, request_id:%s" % (
                e.get_http_status(), e.get_error_code(), e.get_error_message(), e.get_request_id())
        except Exception as e:
            return False, "未知异常"

    def get_list(self, table_name, start_key, end_key, columns_to_get=[], limit=90, cond=None,
                 derection=Direction.FORWARD):
        """
        根据指定范围查询数据
        :param table_name: 字符串，表名
        :param start_key: 字典，查询的开始主键位置
        :param end_key: 字典，查询的结束主键位置
        :param columns_to_get: 列表，属性列
        :param limit: 整型, 查询结果数量
        :param cond: Cond类对象，查询条件
        :param derection: 查询的排列方式，Direction.FORWARD 正序，Direction.BACKWARD 倒序
        :return:
        """
        # 设置范围查询的起始主键。
        inclusive_start_primary_key = []
        for key, value in start_key.items():
            inclusive_start_primary_key.append((key, value))
        # 设置范围查询的结束主键。
        exclusive_end_primary_key = []
        for key, value in end_key.items():
            exclusive_end_primary_key.append((key, value))

        try:
            # 读取数据
            consumed, next_start_primary_key, row_list, next_token = self.client.get_range(
                table_name, derection,
                inclusive_start_primary_key, exclusive_end_primary_key,
                columns_to_get,
                limit,
                column_filter=cond,
                max_version=1,
            )

            all_rows = []
            all_rows.extend(row_list)

            # 打印主键和属性列。
            data = []
            for row in all_rows:
                data_item = {}
                for att in row.primary_key:
                    data_item[att[0]] = att[1]
                if len(columns_to_get) > 0:
                    """如果有指定要返回其他属性列"""
                    for att in row.attribute_columns:
                        data_item[att[0]] = att[1]
                data.append(data_item)

            return {"status": True, "data": data, "token": next_start_primary_key}
        # 客户端异常，一般为参数错误或者网络异常。
        except OTSClientError as e:
            return False, "网络异常, http_status:%d, error_message:%s" % (e.get_http_status(), e.get_error_message())
        # 服务端异常，一般为参数错误或者流控错误。
        except OTSServiceError as e:
            return False, "参数有误, http_status:%d, error_code:%s, error_message:%s, request_id:%s" % (
                e.get_http_status(), e.get_error_code(), e.get_error_message(), e.get_request_id())
        except Exception as e:
            return False, "未知异常"


class TableAPIView(APIView):

    def get(self, request):
        """获取当前仓库中所有的数据表"""
        tables = OTS().list_table()
        print(tables)
        return Response("ok")

    def post(self, request):
        OTS().create_table("user_relation_table", [
            ("user_id", "INTEGER"),
            ("follow_user_id", "INTEGER")
        ])

        OTS().create_table("user_message_table", [
            ("follow_user_id", "INTEGER"),
            ("sequence_id", "INTEGER", PK_AUTO_INCR),
            ("user_id", "INTEGER"),
            ("message_id", "INTEGER"),
        ])

        OTS().create_table("user_message_session_table", [
            ("follow_user_id", "INTEGER"),
            ("last_sequence_id", "INTEGER"),
        ])
        return Response("ok")

    def delete(self, request):
        """删除指定的表"""
        # 删除一张表
        ret = OTS().delete_table("user_message_session_table")
        print(ret)
        # 删除多张表
        ret = OTS().delete_table(["user_message_table", "user_relation_table"])
        print(ret)
        return Response("ok")


from django.utils import timezone as datetime


class DataAPIView(APIView):
    def post(self, request):
        """添加一条数据"""
        ## 主键 = {"主键名":"值","主键名":"值",,,}
        primary_key = {"user_id": 1, 'follow_user_id': 3}

        # 属性列 = {"字段名":"值"}
        attribute_columns = {'timestamp': datetime.now().timestamp()}

        ret = OTS().put_row("user_relation_table", primary_key, attribute_columns)
        print(ret[0])

        return Response("OK")

    def get(self, request):
        """获取一条数据"""
        primary_key = {"user_id": 1, 'follow_user_id': 2}
        ret = OTS().get_row("user_relation_table", primary_key, columns_to_get=["timestamp"])
        return Response(ret)

    def put(self, request):
        primary_key = {"user_id": 1, 'follow_user_id': 2}
        attribute_columns = {"timestamp": 1000866}
        ret = OTS().update_row("user_relation_table", primary_key, attribute_columns)
        return Response(ret)

    def delete(self, request):
        primary_key = {"user_id": 1, 'follow_user_id': 2}
        ret = OTS().delete_row("user_relation_table", primary_key)
        return Response(ret)


class RowAPIView(APIView):
    """多行数据操作"""

    def get0(self, request):
        """根据主键查询多条数据[少用]"""
        primary_key_list = [
            {"user_id": 1, 'follow_user_id': 3},
            {"user_id": 1, 'follow_user_id': 4},
            {"user_id": 1, 'follow_user_id': 5},
        ]

        data = OTS().get_list_0("user_relation_table", primary_key_list, ["timestamp"])

        return Response(data)

    def post(self, request):
        """添加多条数据"""
        primary_key = [
            {"user_id": 1, 'follow_user_id': 5},
            {"user_id": 1, 'follow_user_id': 6},
            {"user_id": 1, 'follow_user_id': 7},
            {"user_id": 1, 'follow_user_id': 8},
        ]
        # 属性列 = {"字段名":"值"}
        attribute_columns = [
            {'timestamp': datetime.now().timestamp()},
            {'timestamp': datetime.now().timestamp()},
            {'timestamp': datetime.now().timestamp()},
            {'timestamp': datetime.now().timestamp()},
        ]

        ret = OTS().add_list("user_relation_table", primary_key, attribute_columns)
        return Response(ret)

    def put(self, request):
        """注意，所谓更新数据，仅仅是更新属性列而已，tablestore中是不提供修改主键的！！！"""
        primary_key = [
            {"user_id": 1, 'follow_user_id': 5},
            {"user_id": 1, 'follow_user_id': 6},
            {"user_id": 1, 'follow_user_id': 7},
            {"user_id": 1, 'follow_user_id': 8},
        ]

        attribute_columns = [
            {'timestamp': datetime.now().timestamp()},
            {'timestamp': datetime.now().timestamp()},
            {'timestamp': datetime.now().timestamp()},
            {'timestamp': datetime.now().timestamp()},
        ]

        ret = OTS().update_list("user_relation_table", primary_key, attribute_columns)
        return Response(ret)

    def delete(self, request):
        primary_key = [
            {"user_id": 1, 'follow_user_id': 5},
            {"user_id": 1, 'follow_user_id': 6},
            {"user_id": 1, 'follow_user_id': 7},
            {"user_id": 1, 'follow_user_id': 8},
        ]
        ret = OTS().delete_list("user_relation_table", primary_key)
        return Response(ret)

    def get(self, request):
        start_key = {"user_id": INF_MIN, 'follow_user_id': INF_MIN}
        end_key = {"user_id": INF_MAX, 'follow_user_id': INF_MAX}

        # 只是按照主键查找数据
        # ret = OTS().get_list("user_relation_table",start_key, end_key,columns_to_get=["timestamp"])
        # 根据条件过滤属性列
        # 第一： 条件查询，字段值的类型严格区分，不同类型，无法查询
        # 第二： 条件查询，只能用于属性列进行，不能使用主键
        cond = SingleColumnCondition("timestamp", 15000033334, ComparatorType.GREATER_THAN)
        ret = OTS().get_list("user_relation_table", start_key, end_key, columns_to_get=["timestamp"], cond=cond)

        return Response(ret)
