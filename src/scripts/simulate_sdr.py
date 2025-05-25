#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Transmisión sin SDR
# Author: tcasaniv
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, pyqtSlot
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
import threading
import transmit_sdr_detect_platform as detect_platform  # embedded python module



class transmit_sdr(gr.top_block, Qt.QWidget):

    def __init__(self, freq_sdr=928e6, samp_rate_sdr=8e6, wavfile=detect_platform.wav_path):
        gr.top_block.__init__(self, "Transmisión sin SDR", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Transmisión sin SDR")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "transmit_sdr")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Parameters
        ##################################################
        self.freq_sdr = freq_sdr
        self.samp_rate_sdr = samp_rate_sdr
        self.wavfile = wavfile

        ##################################################
        # Variables
        ##################################################
        self.wav_path = wav_path = wavfile
        self.volume = volume = 50
        self.max_deviation = max_deviation = 17e3
        self.gain = gain = 0
        self.freq = freq = freq_sdr
        self.fm_rate = fm_rate = 48e3
        self.audio_rate = audio_rate = 11025
        self.activate_amp = activate_amp = False

        ##################################################
        # Blocks
        ##################################################

        self._volume_range = qtgui.Range(0, 300, 1, 50, 200)
        self._volume_win = qtgui.RangeWidget(self._volume_range, self.set_volume, "Volumen", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._volume_win, 0, 1, 1, 2)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.tab_widget = Qt.QTabWidget()
        self.tab_widget_widget_0 = Qt.QWidget()
        self.tab_widget_layout_0 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tab_widget_widget_0)
        self.tab_widget_grid_layout_0 = Qt.QGridLayout()
        self.tab_widget_layout_0.addLayout(self.tab_widget_grid_layout_0)
        self.tab_widget.addTab(self.tab_widget_widget_0, 'APT generado')
        self.tab_widget_widget_1 = Qt.QWidget()
        self.tab_widget_layout_1 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tab_widget_widget_1)
        self.tab_widget_grid_layout_1 = Qt.QGridLayout()
        self.tab_widget_layout_1.addLayout(self.tab_widget_grid_layout_1)
        self.tab_widget.addTab(self.tab_widget_widget_1, 'APT Modulado en FM')
        self.tab_widget_widget_2 = Qt.QWidget()
        self.tab_widget_layout_2 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tab_widget_widget_2)
        self.tab_widget_grid_layout_2 = Qt.QGridLayout()
        self.tab_widget_layout_2.addLayout(self.tab_widget_grid_layout_2)
        self.tab_widget.addTab(self.tab_widget_widget_2, 'Señal transmitiéndose por el SDR')
        self.top_grid_layout.addWidget(self.tab_widget, 2, 0, 5, 4)
        for r in range(2, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._max_deviation_range = qtgui.Range(2.5e3, fm_rate/2, 0.5e3, 17e3, 200)
        self._max_deviation_win = qtgui.RangeWidget(self._max_deviation_range, self.set_max_deviation, "Máxima Desviación FM", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._max_deviation_win, 1, 0, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._freq_msgdigctl_win = qtgui.MsgDigitalNumberControl(lbl='Frecuencia de transmisión', min_freq_hz=1e6, max_freq_hz=6e9, parent=self, thousands_separator=",", background_color="black", fontColor="white", var_callback=self.set_freq, outputmsgname='freq')
        self._freq_msgdigctl_win.setValue(freq_sdr)
        self._freq_msgdigctl_win.setReadOnly(False)
        self.freq = self._freq_msgdigctl_win

        self.top_grid_layout.addWidget(self._freq_msgdigctl_win, 0, 0, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.wavfile_source = blocks.wavfile_source(wav_path, True)
        self.throttle_sdr_gui = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate_sdr, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate_sdr) if "auto" == "time" else int(0.1), 1) )
        self.throttle_fm = blocks.throttle( gr.sizeof_gr_complex*1, fm_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * fm_rate) if "auto" == "time" else int(0.1), 1) )
        self.sdr_gui_freq_sink = qtgui.freq_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            freq, #fc
            samp_rate_sdr, #bw
            "Espectro de la señal transmitiéndose con SDR", #name
            1,
            None # parent
        )
        self.sdr_gui_freq_sink.set_update_time(0.10)
        self.sdr_gui_freq_sink.set_y_axis((-140), 10)
        self.sdr_gui_freq_sink.set_y_label('Ganancia Relativa', 'dB')
        self.sdr_gui_freq_sink.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.sdr_gui_freq_sink.enable_autoscale(False)
        self.sdr_gui_freq_sink.enable_grid(True)
        self.sdr_gui_freq_sink.set_fft_average(1.0)
        self.sdr_gui_freq_sink.enable_axis_labels(True)
        self.sdr_gui_freq_sink.enable_control_panel(True)
        self.sdr_gui_freq_sink.set_fft_window_normalized(False)



        labels = ["Señal APT \nmodulada\nen FM", '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.sdr_gui_freq_sink.set_line_label(i, "Data {0}".format(i))
            else:
                self.sdr_gui_freq_sink.set_line_label(i, labels[i])
            self.sdr_gui_freq_sink.set_line_width(i, widths[i])
            self.sdr_gui_freq_sink.set_line_color(i, colors[i])
            self.sdr_gui_freq_sink.set_line_alpha(i, alphas[i])

        self._sdr_gui_freq_sink_win = sip.wrapinstance(self.sdr_gui_freq_sink.qwidget(), Qt.QWidget)
        self.tab_widget_layout_2.addWidget(self._sdr_gui_freq_sink_win)
        self._gain_range = qtgui.Range(0, 1, 0.01, 0, 200)
        self._gain_win = qtgui.RangeWidget(self._gain_range, self.set_gain, "Ganancia", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._gain_win, 1, 1, 1, 2)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.fm_rational_resampler = filter.rational_resampler_ccc(
                interpolation=int(samp_rate_sdr),
                decimation=int(fm_rate),
                taps=[],
                fractional_bw=0)
        self.control_volume = blocks.multiply_const_ff((volume/100))
        self.audio_sink = audio.sink(12000, '', True)
        self.audio_rational_resampler = filter.rational_resampler_fff(
                interpolation=12000,
                decimation=audio_rate,
                taps=[],
                fractional_bw=0)
        self.audio_gui_freq_sink_0 = qtgui.freq_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            fm_rate, #bw
            "Espectro de la señal APT modulada en FM", #name
            1,
            None # parent
        )
        self.audio_gui_freq_sink_0.set_update_time(0.10)
        self.audio_gui_freq_sink_0.set_y_axis((-140), 10)
        self.audio_gui_freq_sink_0.set_y_label('Ganancia Relativa', 'dB')
        self.audio_gui_freq_sink_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.audio_gui_freq_sink_0.enable_autoscale(False)
        self.audio_gui_freq_sink_0.enable_grid(True)
        self.audio_gui_freq_sink_0.set_fft_average(1.0)
        self.audio_gui_freq_sink_0.enable_axis_labels(True)
        self.audio_gui_freq_sink_0.enable_control_panel(True)
        self.audio_gui_freq_sink_0.set_fft_window_normalized(False)



        labels = ["Señal APT\nmodulada\nen FM", '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.audio_gui_freq_sink_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.audio_gui_freq_sink_0.set_line_label(i, labels[i])
            self.audio_gui_freq_sink_0.set_line_width(i, widths[i])
            self.audio_gui_freq_sink_0.set_line_color(i, colors[i])
            self.audio_gui_freq_sink_0.set_line_alpha(i, alphas[i])

        self._audio_gui_freq_sink_0_win = sip.wrapinstance(self.audio_gui_freq_sink_0.qwidget(), Qt.QWidget)
        self.tab_widget_layout_1.addWidget(self._audio_gui_freq_sink_0_win)
        self.audio_gui_freq_sink = qtgui.freq_sink_f(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            12000, #bw
            "Espectro de la señal Automatic Picture Transmission (APT)", #name
            1,
            None # parent
        )
        self.audio_gui_freq_sink.set_update_time(0.10)
        self.audio_gui_freq_sink.set_y_axis((-140), 10)
        self.audio_gui_freq_sink.set_y_label('Ganancia Relativa', 'dB')
        self.audio_gui_freq_sink.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.audio_gui_freq_sink.enable_autoscale(False)
        self.audio_gui_freq_sink.enable_grid(True)
        self.audio_gui_freq_sink.set_fft_average(1.0)
        self.audio_gui_freq_sink.enable_axis_labels(True)
        self.audio_gui_freq_sink.enable_control_panel(True)
        self.audio_gui_freq_sink.set_fft_window_normalized(False)


        self.audio_gui_freq_sink.set_plot_pos_half(not False)

        labels = ["APT\n(imagen\n en AM)", '', '', '', '',
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
        self.tab_widget_layout_0.addWidget(self._audio_gui_freq_sink_win)
        self.analog_nbfm_tx = analog.nbfm_tx(
        	audio_rate=12000,
        	quad_rate=int(fm_rate),
        	tau=(75e-6),
        	max_dev=max_deviation,
        	fh=(-1.0),
                )
        self.analog_nbfm_rx = analog.nbfm_rx(
        	audio_rate=12000,
        	quad_rate=int(fm_rate),
        	tau=(75e-6),
        	max_dev=max_deviation,
          )
        # Create the options list
        self._activate_amp_options = [False, True]
        # Create the labels list
        self._activate_amp_labels = ['Desactivado', 'Activado (+11 dB)']
        # Create the combo box
        # Create the radio buttons
        self._activate_amp_group_box = Qt.QGroupBox("Amplificador Tx (Solo HackRF)" + ": ")
        self._activate_amp_box = Qt.QVBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._activate_amp_button_group = variable_chooser_button_group()
        self._activate_amp_group_box.setLayout(self._activate_amp_box)
        for i, _label in enumerate(self._activate_amp_labels):
            radio_button = Qt.QRadioButton(_label)
            self._activate_amp_box.addWidget(radio_button)
            self._activate_amp_button_group.addButton(radio_button, i)
        self._activate_amp_callback = lambda i: Qt.QMetaObject.invokeMethod(self._activate_amp_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._activate_amp_options.index(i)))
        self._activate_amp_callback(self.activate_amp)
        self._activate_amp_button_group.buttonClicked[int].connect(
            lambda i: self.set_activate_amp(self._activate_amp_options[i]))
        self.top_grid_layout.addWidget(self._activate_amp_group_box, 0, 3, 2, 1)
        for r in range(0, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_nbfm_rx, 0), (self.audio_sink, 0))
        self.connect((self.analog_nbfm_tx, 0), (self.analog_nbfm_rx, 0))
        self.connect((self.analog_nbfm_tx, 0), (self.fm_rational_resampler, 0))
        self.connect((self.analog_nbfm_tx, 0), (self.throttle_fm, 0))
        self.connect((self.audio_rational_resampler, 0), (self.analog_nbfm_tx, 0))
        self.connect((self.audio_rational_resampler, 0), (self.audio_gui_freq_sink, 0))
        self.connect((self.control_volume, 0), (self.audio_rational_resampler, 0))
        self.connect((self.fm_rational_resampler, 0), (self.throttle_sdr_gui, 0))
        self.connect((self.throttle_fm, 0), (self.audio_gui_freq_sink_0, 0))
        self.connect((self.throttle_sdr_gui, 0), (self.sdr_gui_freq_sink, 0))
        self.connect((self.wavfile_source, 0), (self.control_volume, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "transmit_sdr")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_freq_sdr(self):
        return self.freq_sdr

    def set_freq_sdr(self, freq_sdr):
        self.freq_sdr = freq_sdr
        self._freq_msgdigctl_win.setValue(self.freq_sdr)

    def get_samp_rate_sdr(self):
        return self.samp_rate_sdr

    def set_samp_rate_sdr(self, samp_rate_sdr):
        self.samp_rate_sdr = samp_rate_sdr
        self.sdr_gui_freq_sink.set_frequency_range(self.freq, self.samp_rate_sdr)
        self.throttle_sdr_gui.set_sample_rate(self.samp_rate_sdr)

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

    def get_max_deviation(self):
        return self.max_deviation

    def set_max_deviation(self, max_deviation):
        self.max_deviation = max_deviation
        self.analog_nbfm_rx.set_max_deviation(self.max_deviation)
        self.analog_nbfm_tx.set_max_deviation(self.max_deviation)

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.sdr_gui_freq_sink.set_frequency_range(self.freq, self.samp_rate_sdr)

    def get_fm_rate(self):
        return self.fm_rate

    def set_fm_rate(self, fm_rate):
        self.fm_rate = fm_rate
        self.audio_gui_freq_sink_0.set_frequency_range(0, self.fm_rate)
        self.throttle_fm.set_sample_rate(self.fm_rate)

    def get_audio_rate(self):
        return self.audio_rate

    def set_audio_rate(self, audio_rate):
        self.audio_rate = audio_rate

    def get_activate_amp(self):
        return self.activate_amp

    def set_activate_amp(self, activate_amp):
        self.activate_amp = activate_amp
        self._activate_amp_callback(self.activate_amp)



def argument_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "--freq-sdr", dest="freq_sdr", type=eng_float, default=eng_notation.num_to_str(float(928e6)),
        help="Set Frecuencia TX SDR [default=%(default)r]")
    parser.add_argument(
        "--samp-rate-sdr", dest="samp_rate_sdr", type=eng_float, default=eng_notation.num_to_str(float(8e6)),
        help="Set Frecuencia de muestro TX SDR [default=%(default)r]")
    parser.add_argument(
        "--wavfile", dest="wavfile", type=str, default=detect_platform.wav_path,
        help="Set Ruta archivo WAV [default=%(default)r]")
    return parser


def main(top_block_cls=transmit_sdr, options=None):
    if options is None:
        options = argument_parser().parse_args()

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls(freq_sdr=options.freq_sdr, samp_rate_sdr=options.samp_rate_sdr, wavfile=options.wavfile)

    tb.start()
    tb.flowgraph_started.set()

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
