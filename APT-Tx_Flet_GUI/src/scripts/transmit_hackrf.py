#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: transmit_hackrf
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
import sip
import transmit_hackrf_detect_platform as detect_platform  # embedded python module



class transmit_hackrf(gr.top_block, Qt.QWidget):

    def __init__(self, samp_rate_sdr=8e6, wavfile=detect_platform.wav_path):
        gr.top_block.__init__(self, "transmit_hackrf", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("transmit_hackrf")
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

        self.settings = Qt.QSettings("GNU Radio", "transmit_hackrf")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Parameters
        ##################################################
        self.samp_rate_sdr = samp_rate_sdr
        self.wavfile = wavfile

        ##################################################
        # Variables
        ##################################################
        self.wav_path = wav_path = wavfile
        self.volume = volume = 50
        self.gain_sdr_tx = gain_sdr_tx = 0
        self.freq = freq = 928e6
        self.fm_rate = fm_rate = 48e3
        self.audio_rate = audio_rate = 11025

        ##################################################
        # Blocks
        ##################################################

        self._volume_range = qtgui.Range(0, 300, 1, 50, 200)
        self._volume_win = qtgui.RangeWidget(self._volume_range, self.set_volume, "Volumen", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._volume_win, 0, 2, 1, 2)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.wavfile_source = blocks.wavfile_source(wav_path, True)
        self.throttle_fm_gui = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate_sdr, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate_sdr) if "auto" == "time" else int(0.1), 1) )
        self.rational_resampler_0 = filter.rational_resampler_fff(
                interpolation=12000,
                decimation=audio_rate,
                taps=[],
                fractional_bw=0)
        self.rational_resampler = filter.rational_resampler_ccc(
                interpolation=int(samp_rate_sdr),
                decimation=int(fm_rate),
                taps=[],
                fractional_bw=0)
        self._gain_sdr_tx_range = qtgui.Range(0, 47, 1, 0, 200)
        self._gain_sdr_tx_win = qtgui.RangeWidget(self._gain_sdr_tx_range, self.set_gain_sdr_tx, "Ganancia Tx", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._gain_sdr_tx_win, 0, 4, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 5):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._freq_msgdigctl_win = qtgui.MsgDigitalNumberControl(lbl='Frecuencia de transmisión', min_freq_hz=88e6, max_freq_hz=1700e6, parent=self, thousands_separator=",", background_color="black", fontColor="white", var_callback=self.set_freq, outputmsgname='freq')
        self._freq_msgdigctl_win.setValue(928e6)
        self._freq_msgdigctl_win.setReadOnly(False)
        self.freq = self._freq_msgdigctl_win

        self.top_grid_layout.addWidget(self._freq_msgdigctl_win, 0, 0, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.fm_gui_freq_sink = qtgui.freq_sink_c(
            4096, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate_sdr, #bw
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
        self.audio_sink = audio.sink(12000, '', True)
        self.analog_nbfm_tx = analog.nbfm_tx(
        	audio_rate=12000,
        	quad_rate=int(fm_rate),
        	tau=(75e-6),
        	max_dev=17e3,
        	fh=(-1.0),
                )
        self.analog_nbfm_rx = analog.nbfm_rx(
        	audio_rate=12000,
        	quad_rate=int(fm_rate),
        	tau=(75e-6),
        	max_dev=17e3,
          )


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_nbfm_rx, 0), (self.audio_sink, 0))
        self.connect((self.analog_nbfm_tx, 0), (self.analog_nbfm_rx, 0))
        self.connect((self.analog_nbfm_tx, 0), (self.rational_resampler, 0))
        self.connect((self.control_volume, 0), (self.rational_resampler_0, 0))
        self.connect((self.rational_resampler, 0), (self.throttle_fm_gui, 0))
        self.connect((self.rational_resampler_0, 0), (self.analog_nbfm_tx, 0))
        self.connect((self.throttle_fm_gui, 0), (self.fm_gui_freq_sink, 0))
        self.connect((self.wavfile_source, 0), (self.control_volume, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "transmit_hackrf")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_samp_rate_sdr(self):
        return self.samp_rate_sdr

    def set_samp_rate_sdr(self, samp_rate_sdr):
        self.samp_rate_sdr = samp_rate_sdr
        self.fm_gui_freq_sink.set_frequency_range(0, self.samp_rate_sdr)
        self.throttle_fm_gui.set_sample_rate(self.samp_rate_sdr)

    def get_wavfile(self):
        return self.wavfile

    def set_wavfile(self, wavfile):
        self.wavfile = wavfile
        self.set_wav_path(self.wavfile)

    def get_wav_path(self):
        return self.wav_path

    def set_wav_path(self, wav_path):
        self.wav_path = wav_path

    def get_volume(self):
        return self.volume

    def set_volume(self, volume):
        self.volume = volume
        self.control_volume.set_k((self.volume/100))

    def get_gain_sdr_tx(self):
        return self.gain_sdr_tx

    def set_gain_sdr_tx(self, gain_sdr_tx):
        self.gain_sdr_tx = gain_sdr_tx

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq

    def get_fm_rate(self):
        return self.fm_rate

    def set_fm_rate(self, fm_rate):
        self.fm_rate = fm_rate

    def get_audio_rate(self):
        return self.audio_rate

    def set_audio_rate(self, audio_rate):
        self.audio_rate = audio_rate



def argument_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "-s", "--samp-rate-sdr", dest="samp_rate_sdr", type=eng_float, default=eng_notation.num_to_str(float(8e6)),
        help="Set samp_rate_sdr [default=%(default)r]")
    parser.add_argument(
        "-f", "--wavfile", dest="wavfile", type=str, default=detect_platform.wav_path,
        help="Set /home/tcasaniv/APT-Tx_Files/apt_generated_audio.wav [default=%(default)r]")
    return parser


def main(top_block_cls=transmit_hackrf, options=None):
    if options is None:
        options = argument_parser().parse_args()

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls(samp_rate_sdr=options.samp_rate_sdr, wavfile=options.wavfile)

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
