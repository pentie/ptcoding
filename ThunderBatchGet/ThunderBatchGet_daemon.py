import os
import sys
import fcntl
import time
import logging
from collections import deque 
import threading
from threading import Thread
from subprocess import Popen, PIPE
from select import select
import select

import bottle
bottle.debug(True)

from bottle import route, run, request, view, abort
import Cookie
import cStringIO

logging.basicConfig(filename = "/tmp/thunderbatch.log",
        format = "%(asctime)s %(threadName)s(%(thread)s):%(name)s:%(message)s",
                            level = logging.INFO)

DEFAULT_DOWN_DIR = os.path.expanduser("~/Downloads")

if not os.path.isdir(DEFAULT_DOWN_DIR):
    DEFAULT_DOWN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Downloads")
    if not os.path.exists(DEFAULT_DOWN_DIR):
        os.mkdir(DEFAULT_DOWN_DIR)


logger = logging.getLogger()

task_mgr = None

def LogException(func):
    def __check(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            logger.info("Exception", exc_info = True)
            raise
    return __check


class DownloadThread(Thread):

    def __init__(self, cmd_args, std_deque, err_deque, cwd = None):
        super(DownloadThread, self).__init__(name = type(self).__name__)
        self.logger = logging.getLogger(type(self).__name__)
        self.daemon = True

        self.cmd_args = cmd_args
        self.cwd = cwd
        self.std_deque = std_deque
        self.err_deque = err_deque
        self.retcode = None
        self.subprocess = None

    def run(self):
        logger = self.logger
        logger.info("init")
        self.subprocess = proc = Popen(self.cmd_args, bufsize = 4096, cwd = self.cwd, stdout=PIPE, stderr=PIPE, close_fds=True)
        out, err= proc.stdout, proc.stderr
        fn_dict = {out.fileno():self.std_deque, err.fileno():self.err_deque}

        epoll = select.epoll()
        epoll.register(out.fileno(), select.EPOLLIN)
        epoll.register(err.fileno(), select.EPOLLIN)
         
        #async
        fcntl.fcntl(out, fcntl.F_SETFL, os.O_NONBLOCK)
        fcntl.fcntl(err, fcntl.F_SETFL, os.O_NONBLOCK)

        try:
            logger.info("run cmd: '%s'" % "' '".join(self.cmd_args))
            exit_flag = False

            while True:
                if proc.poll() is not None:
                    exit_flag = True

                events = epoll.poll()
                for fileno, event in events:
                    if event & select.EPOLLIN:
                        dq = fn_dict[fileno]
                        o = os.read(fileno, 65536)
                        dq.append(o)

                if exit_flag:
                    ret = self.retcode = proc.returncode
                    logger.info("wget ended. exit code: '%d'" % ret)
                    break

        except Exception, e:
            logger.info(str(e), exc_info = True)
            raise

        finally:
            epoll.unregister(err.fileno())
            epoll.unregister(out.fileno())
            epoll.close()
            out.close()
            err.close()

            #time.sleep(0.1)


    @property
    def is_wget_error(self):
        retcode = self.retcode
        return (not self.is_alive()) and (retcode is not None) and (retcode != 0) and (retcode != 3)

    is_subprocess_exit_0 = property(lambda s:s.retcode == 0)
    is_subprocess_finished = property(lambda s:s.subprocess.poll() is not None)

    def suicide(self):
        log = self.logger
        log.info("thread suicide")
        if self.is_alive():
            if self.subprocess.poll() is None:
                log.info("subprocess living.. terminate it")
                self.subprocess.terminate()
                while self.subprocess.poll() is None:
                    log.info("wait for subprocess end.")
                    time.sleep(0.5)

class DownloadTask(object):

    uid = None
    tasktype = None
    filename = None
    dl_dir = None
    dl_url = None
    dl_headers = None
    cookies_values = None
    retry_time = 0
    dl_thread = None

    __str__ = lambda s : "[uid='%s',tasktype='%s',filename='%s',retry_time='%s',dl_thread='%s',,,finished='%s',need_retry='%s']" % (s.uid, s.tasktype, s.filename, s.retry_time, s.dl_thread, s.is_task_finished, s.need_retry)

    def __init__(self, *args, **kw):
        self.__dict__.update(**kw)
        self.logger = logging.getLogger(type(self).__name__)

        self.uid = str(time.time()).replace('.', '')
        self.dl_headers = "Cookie: " + "".join(map(lambda s:"%s=%s; " % s, self.cookies_values))
        self.std_deque = deque(maxlen = 8 * 1024)
        self.err_deque = deque(maxlen = 8 * 1024)

    def start_thread(self):
        self.retry_time += 1
        self.logger.info("thread start")
        wget_cmd = ['/usr/bin/wget', '--continue', '--header', self.dl_headers, '-O', self.filename, 
                '--progress=dot', self.dl_url]
        self.dl_thread = DownloadThread(wget_cmd, self.std_deque, self.err_deque, self.dl_dir)
        self.dl_thread.start()

    def force_restart(self, reset_cnt = False):
        self.logger.info("call force_restart, ")
        log = self.logger

        if self.dl_thread is not None and self.dl_thread.is_alive():
            self.dl_thread.suicide()
            log.info("thread is alive, join")
            self.dl_thread.join()

        self.dl_thread = None
        if reset_cnt:
            self.retry_time = 0
        self.start_thread()
        log.info("thread restarted, id :%s" % str(self.dl_thread.ident))

    @property
    def need_retry(self):
        if self.dl_thread is None:
            return False
        wget_err = self.dl_thread.is_wget_error
        filepath = os.path.join(self.dl_dir, self.filename)
        log = self.logger
        if wget_err:
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0 and self.retry_time > 5:
                log.info("task '%s' might finished. if not, try remove this file: '%s'" % (self.uid, filepath))
                return False
            elif self.retry_time > 10:
                log.info("task '%s' failed for 10 times. skip forever" % str(self.uid))
                return False

        return wget_err

    @property
    def is_task_finished(self):
        if (self.dl_thread is None):
            return True
        elif self.dl_thread.is_subprocess_exit_0 and not self.dl_thread.is_alive():
            self.dl_thread = None
            self.logger.info("task %s finished, remove thread obj" % self.uid)
            return True
        else:
            return self.dl_thread.is_subprocess_finished

    @property
    def status(self):
        thread = self.dl_thread
        if thread is None:
            return "Done"

        retcode = self.dl_thread.retcode
        status = ''
        if thread.is_alive():
            status = "Running"
        else:
            if retcode == 0:
                status = "Done"
            elif retcode == 3:
                status = "IO Error"
            else:
                status = "Error"

        return status

    report_dict = property(lambda s:dict(status = s.status, 
                                        retry_time = s.retry_time, 
                                        is_task_finished = s.is_task_finished))

    def log_output(self):
        log = ''
        self.logger.debug("len %d,%d" % (len(self.std_deque), len(self.err_deque)))
        for queue in (self.std_deque, self.err_deque):
            if len(queue) > 0:
                output = cStringIO.StringIO()
                while True:
                    try:
                        line = queue.popleft()
                        output.write(line)
                    except IndexError:
                        break
                log += output.getvalue()
                output.close()

        return log


class TaskMointorThread(Thread):

    def __init__(self, task_mgr):
        super(TaskMointorThread, self).__init__(name = type(self).__name__)
        self.logger = logging.getLogger(type(self).__name__)
        self.daemon = True
        self.task_mgr = task_mgr

    def run(self):
        logger = self.logger
        task_pool = self.task_mgr.thread_pool

        logger.info("init")

        while True:
            keys = tuple(task_pool.keys())
            for k in keys:
                t = task_pool[k]
                logger.debug(str(t))
                if t.is_task_finished and t.need_retry:
                    logger.info("retry task " + str(t.uid))
                    t.force_restart(reset_cnt = False)
            time.sleep(3)


class ThunderTaskManager(object):

    def __init__(self):
        self.logger = logging.getLogger(type(self).__name__)
        self.thread_pool = {}

    def new_wget_task(self, tasktype, filename, dl_url, cookies_values):
        task = DownloadTask(tasktype = tasktype,
                        filename = filename,
                        dl_dir = DEFAULT_DOWN_DIR,
                        dl_url = dl_url,
                        cookies_values = cookies_values,
                        )
        uid = task.uid
        self.thread_pool[uid] = task
        task.start_thread()
        return uid

    def force_restart(self, uid):
        self.thread_pool[uid].force_restart(reset_cnt = True)

    def list_all_tasks(self):
        p = self.thread_pool
        self.logger.debug("list all keys: " + str(self.thread_pool.keys()))
        return map(lambda k:dict(uid = p[k].uid, 
                                tasktype = p[k].tasktype,
                                filename = p[k].filename, 
                                status = p[k].status), 
                   sorted(self.thread_pool.keys()))


@route("/thunder_single_task")
@LogException
def thunder_single_task():
    filename = request.GET.get("name")
    dl_url = request.GET.get("url")
    cookies_str = request.GET.get("cookies")
    cookie = Cookie.BaseCookie(cookies_str)
    gdriveid = cookie["gdriveid"].value
    tid = task_mgr.new_wget_task("thunder", filename, dl_url, [("gdriveid", gdriveid)])
    return dict(tid = tid)

@route("/qq_single_task")
@LogException
def qq_single_task():
    filename = request.GET.get("name")
    dl_url = request.GET.get("url")
    cookies_str = request.GET.get("cookies")
    cookie = Cookie.BaseCookie(cookies_str)
    tid = task_mgr.new_wget_task("qq", filename, dl_url, [("FTN5K", cookie["FTN5K"].value)])
    return dict(tid = tid)

@route("/list_all_tasks")
@LogException
def list_all_tasks():
    return dict(tasks = task_mgr.list_all_tasks())


@route("/query_task_log/:tid")
@LogException
def query_task_log(tid = None):
    assert tid is not None, "need tid"

    task = task_mgr.thread_pool.get(tid)
    if task is None:
        abort(404, "taskid not found, " + tid)

    line = task.log_output()
    ret = task.report_dict
    ret.update(line = line)
    return ret

@route("/force_restart/:tid")
@LogException
def force_restart(tid = None):
    assert tid is not None, "need tid"
    task_mgr.force_restart(tid)
    return ""



@route("/")
@view('mointor')
def root():
    return {}


if __name__ == "__main__":


    task_mgr = ThunderTaskManager()
    mointor = TaskMointorThread(task_mgr)
    mointor.start()

    import webbrowser
    webbrowser.open_new_tab("http://127.0.0.1:8080")
    print "Default Download Dir: '%s'" % DEFAULT_DOWN_DIR

    run(host='0.0.0.0', port=8080)


import unittest

class test_wget(unittest.TestCase):
    def setUp(self):

        import shlex
        cmd = 'wget -O /dev/null --progress=dot http://ftp.tw.debian.org/debian/ls-lR.gz'
        cmd = 'wget -O /dev/null --progress=dot http://ftp.tw.debian.org/debian/ls-lR.patch.gz'

        self.shell_cmd = shlex.split(cmd)
        print self.shell_cmd

    def test_wget(self):
        t = DownloadThread(self.shell_cmd)
        t.start()

        while True:
            try:
                c, o = t.pop()
                print c, o

            except IndexError:
                if not t.is_alive():
                    break

                time.sleep(.1)


    def test_notget(self):

        t = DownloadThread(self.shell_cmd)
        t.start()
        t.join()

    def test_taskmgr(self):

        filename = "13. Hiding My Heart.mp3"
        dl_url = "http://gdl.lixian.vip.xunlei.com/download?fid=qyh37P2CIFsIwt/RgbLulXGzJo27TH8AAAAAAHLX9VaTzNJL1DkuNS5iEzxbyGLZ&mid=666&threshold=150&tid=F4F3C6EE85C70547FDA4D027E0E895D5&srcid=4&verno=1&g=72D7F55693CCD24BD4392E352E62133C5BC862D9&scn=t7&i=71F8AE377D07F36D04350171D3BB8FD33E162150&t=6&ui=169602995&ti=42518759750&s=8342715&m=0&n=015002CA7F486964690F56C41279204865004390716D703300"
        gdriveid = "7617B8D05D955EA55C05EF3908D8162F"

        m = ThunderTaskManager()
        tid = m.new_thunder_task(filename, dl_url, gdriveid)
        t = m.thread_pool[tid].dl_thread

        while True:
            try:
                c, o = t.pop()
                if c == "OUT":
                    sys.stdout.write(o)
                else:
                    print c, o

            except IndexError:
                if not t.is_alive():
                    break

                time.sleep(.1)



