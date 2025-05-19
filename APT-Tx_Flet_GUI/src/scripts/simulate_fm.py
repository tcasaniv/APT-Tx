#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: simulate_fm
# Author: tcasaniv
# GNU Radio version: 3.10.9.2

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from gnuradio import analog
from gnuradio import audio
from gnuradio import blocks
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import simulate_fm_detect_platform as detect_platform  # embedded python module
import sip



class simulate_fm(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "simulate_fm", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("simulate_fm")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "simulate_fm")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Variables
        ##################################################
        self.audio_rate = audio_rate = 11025
        self.wav_path = wav_path = detect_platform.wav_path
        self.volume = volume = 50
        self.fm_rate = fm_rate = audio_rate*3

        ##################################################
        # Blocks
        ##################################################

        self._volume_range = qtgui.Range(0, 100, 1, 50, 200)
        self._volume_win = qtgui.RangeWidget(self._volume_range, self.set_volume, "Volumen", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._volume_win)
        self.wavfile_source = blocks.wavfile_source(wav_path, True)
        self.throttle_fm_gui = blocks.throttle( gr.sizeof_gr_complex*1, (fm_rate*2), True, 0 if "auto" == "auto" else max( int(float(0.1) * (fm_rate*2)) if "auto" == "time" else int(0.1), 1) )
        self.throttle_audio_gui = blocks.throttle( gr.sizeof_float*1, audio_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * audio_rate) if "auto" == "time" else int(0.1), 1) )
        self.rational_resampler = filter.rational_resampler_ccc(
                interpolation=2,
                decimation=1,
                taps=[],
                fractional_bw=0)
        self.fm_gui_freq_sink = qtgui.freq_sink_c(
            4096, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            (fm_rate*2), #bw
            "", #name
            1,
            None # parent
        )
        self.fm_gui_freq_sink.set_update_time(0.10)
        self.fm_gui_freq_sink.set_y_axis((-140), 10)
        self.fm_gui_freq_sink.set_y_label('Relative Gain', 'dB')
        self.fm_gui_freq_sink.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.fm_gui_freq_sink.enable_autoscale(False)
        self.fm_gui_freq_sink.enable_grid(True)
        self.fm_gui_freq_sink.set_fft_average(1.0)
        self.fm_gui_freq_sink.enable_axis_labels(True)
        self.fm_gui_freq_sink.enable_control_panel(True)
        self.fm_gui_freq_sink.set_fft_window_normalized(False)



        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.fm_gui_freq_sink.set_line_label(i, "Data {0}".format(i))
            else:
                self.fm_gui_freq_sink.set_line_label(i, labels[i])
            self.fm_gui_freq_sink.set_line_width(i, widths[i])
            self.fm_gui_freq_sink.set_line_color(i, colors[i])
            self.fm_gui_freq_sink.set_line_alpha(i, alphas[i])

        self._fm_gui_freq_sink_win = sip.wrapinstance(self.fm_gui_freq_sink.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._fm_gui_freq_sink_win)
        self.control_volume = blocks.multiply_const_ff((volume/100))
        self.audio_sink = audio.sink(audio_rate, '', True)
        self.audio_gui_time_sink = qtgui.time_sink_f(
            2048, #size
            audio_rate, #samp_rate
            "", #name
            1, #number of inputs
            None # parent
        )
        self.audio_gui_time_sink.set_update_time(0.01)
        self.audio_gui_time_sink.set_y_axis(-1, 1)

        self.audio_gui_time_sink.set_y_label('Amplitude', "")

        self.audio_gui_time_sink.enable_tags(True)
        self.audio_gui_time_sink.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.audio_gui_time_sink.enable_autoscale(False)
        self.audio_gui_time_sink.enable_grid(True)
        self.audio_gui_time_sink.enable_axis_labels(True)
        self.audio_gui_time_sink.enable_control_panel(True)
        self.audio_gui_time_sink.enable_stem_plot(False)


        labels = ['Signal 1', 'Signal 2', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.audio_gui_time_sink.set_line_label(i, "Data {0}".format(i))
            else:
                self.audio_gui_time_sink.set_line_label(i, labels[i])
            self.audio_gui_time_sink.set_line_width(i, widths[i])
            self.audio_gui_time_sink.set_line_color(i, colors[i])
            self.audio_gui_time_sink.set_line_style(i, styles[i])
            self.audio_gui_time_sink.set_line_marker(i, markers[i])
            self.audio_gui_time_sink.set_line_alpha(i, alphas[i])

        self._audio_gui_time_sink_win = sip.wrapinstance(self.audio_gui_time_sink.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._audio_gui_time_sink_win)
        self.audio_gui_freq_sink = qtgui.freq_sink_f(
            2048, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            audio_rate, #bw
            "", #name
            1,
            None # parent
        )
        self.audio_gui_freq_sink.set_update_time(0.10)
        self.audio_gui_freq_sink.set_y_axis((-140), 10)
        self.audio_gui_freq_sink.set_y_label('Relative Gain', 'dB')
        self.audio_gui_freq_sink.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.audio_gui_freq_sink.enable_autoscale(False)
        self.audio_gui_freq_sink.enable_grid(True)
        self.audio_gui_freq_sink.set_fft_average(1.0)
        self.audio_gui_freq_sink.enable_axis_labels(True)
        self.audio_gui_freq_sink.enable_control_panel(True)
        self.audio_gui_freq_sink.set_fft_window_normalized(False)


        self.audio_gui_freq_sink.set_plot_pos_half(not False)

        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.audio_gui_freq_sink.set_line_label(i, "Data {0}".format(i))
            else:
                self.audio_gui_freq_sink.set_line_label(i, labels[i])
            self.audio_gui_freq_sink.set_line_width(i, widths[i])
            self.audio_gui_freq_sink.set_line_color(i, colors[i])
            self.audio_gui_freq_sink.set_line_alpha(i, alphas[i])

        self._audio_gui_freq_sink_win = sip.wrapinstance(self.audio_gui_freq_sink.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._audio_gui_freq_sink_win)
        self.analog_nbfm_tx = analog.nbfm_tx(
        	audio_rate=audio_rate,
        	quad_rate=fm_rate,
        	tau=(75e-6),
        	max_dev=17e3,
        	fh=(-1.0),
                )
        self.analog_nbfm_rx = analog.nbfm_rx(
        	audio_rate=audio_rate,
        	quad_rate=fm_rate,
        	tau=(75e-6),
        	max_dev=17e3,
          )


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_nbfm_rx, 0), (self.audio_sink, 0))
        self.connect((self.analog_nbfm_rx, 0), (self.throttle_audio_gui, 0))
        self.connect((self.analog_nbfm_tx, 0), (self.analog_nbfm_rx, 0))
        self.connect((self.analog_nbfm_tx, 0), (self.rational_resampler, 0))
        self.connect((self.control_volume, 0), (self.analog_nbfm_tx, 0))
        self.connect((self.rational_resampler, 0), (self.throttle_fm_gui, 0))
        self.connect((self.throttle_audio_gui, 0), (self.audio_gui_freq_sink, 0))
        self.connect((self.throttle_audio_gui, 0), (self.audio_gui_time_sink, 0))
        self.connect((self.throttle_fm_gui, 0), (self.fm_gui_freq_sink, 0))
        self.connect((self.wavfile_source, 0), (self.control_volume, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "simulate_fm")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_audio_rate(self):
        return self.audio_rate

    def set_audio_rate(self, audio_rate):
        self.audio_rate = audio_rate
        self.set_fm_rate(self.audio_rate*3)
        self.audio_gui_freq_sink.set_frequency_range(0, self.audio_rate)
        self.audio_gui_time_sink.set_samp_rate(self.audio_rate)
        self.throttle_audio_gui.set_sample_rate(self.audio_rate)

    def get_wav_path(self):
        return self.wav_path

    def set_wav_path(self, wav_path):
        self.wav_path = wav_path

    def get_volume(self):
        return self.volume

    def set_volume(self, volume):
        self.volume = volume
        self.control_volume.set_k((self.volume/100))

    def get_fm_rate(self):
        return self.fm_rate

    def set_fm_rate(self, fm_rate):
        self.fm_rate = fm_rate
        self.fm_gui_freq_sink.set_frequency_range(0, (self.fm_rate*2))
        self.throttle_fm_gui.set_sample_rate((self.fm_rate*2))




def main(top_block_cls=simulate_fm, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
