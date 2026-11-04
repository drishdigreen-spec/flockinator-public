#include "sdkconfig.h"
#if CONFIG_CODEC_I2C_BACKWARD_COMPATIBLE
#error "Codec must use the new I2C master driver shared with sensors"
#endif
#include "audio.h"
#include "sensors.h"
#include "driver/i2s_std.h"
#include "esp_codec_dev.h"
#include "esp_codec_dev_defaults.h"
#include "esp_timer.h"
#include <cmath>
static i2s_chan_handle_t tx,rx;
static esp_codec_dev_handle_t speaker,mics;
static bool speaker_ok=false,mics_ok=false;
static esp_err_t stream_error=ESP_ERR_INVALID_STATE;
static double rms[2]{},dc[2]{};
static int peak[2]{},clipped[2]{};
static uint32_t captured=0,observed=0;
void audio_init() {
    if(!sensor_bus()) return;
    i2s_chan_config_t channels=I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0,I2S_ROLE_MASTER);
    channels.auto_clear=true;
    if(i2s_new_channel(&channels,&tx,&rx)!=ESP_OK) return;
    i2s_std_config_t config{};
    config.clk_cfg=I2S_STD_CLK_DEFAULT_CONFIG(16000);
    config.slot_cfg=I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_16BIT,I2S_SLOT_MODE_STEREO);
    config.gpio_cfg.mclk=GPIO_NUM_12; config.gpio_cfg.bclk=GPIO_NUM_43; config.gpio_cfg.ws=GPIO_NUM_38;
    config.gpio_cfg.dout=GPIO_NUM_21; config.gpio_cfg.din=GPIO_NUM_39;
    if(i2s_channel_init_std_mode(tx,&config)!=ESP_OK || i2s_channel_init_std_mode(rx,&config)!=ESP_OK) return;
    if(i2s_channel_enable(tx)!=ESP_OK || i2s_channel_enable(rx)!=ESP_OK) return;
    audio_codec_i2s_cfg_t data_cfg{}; data_cfg.port=I2S_NUM_0; data_cfg.tx_handle=tx; data_cfg.rx_handle=rx;
    auto* data=audio_codec_new_i2s_data(&data_cfg); if(!data) return;
    audio_codec_i2c_cfg_t ctrl_cfg{}; ctrl_cfg.port=I2C_NUM_0; ctrl_cfg.bus_handle=sensor_bus(); ctrl_cfg.addr=ES8311_CODEC_DEFAULT_ADDR;
    auto* output=audio_codec_new_i2c_ctrl(&ctrl_cfg); if(!output) return;
    es8311_codec_cfg_t dac{}; dac.ctrl_if=output; dac.gpio_if=audio_codec_new_gpio(); dac.codec_mode=ESP_CODEC_DEV_WORK_MODE_DAC;
    dac.pa_pin=GPIO_NUM_11; dac.use_mclk=true; dac.hw_gain.pa_voltage=3.3; dac.hw_gain.codec_dac_voltage=3.3;
    esp_codec_dev_cfg_t dev{}; dev.dev_type=ESP_CODEC_DEV_TYPE_OUT; dev.data_if=data; dev.codec_if=es8311_codec_new(&dac);
    if(dev.codec_if) speaker=esp_codec_dev_new(&dev);
    ctrl_cfg.addr=ES7210_CODEC_DEFAULT_ADDR;
    es7210_codec_cfg_t adc{}; adc.ctrl_if=audio_codec_new_i2c_ctrl(&ctrl_cfg);
    adc.mic_selected=ES7120_SEL_MIC1|ES7120_SEL_MIC2; adc.mclk_div=256;
    dev.dev_type=ESP_CODEC_DEV_TYPE_IN; dev.codec_if=adc.ctrl_if?es7210_codec_new(&adc):nullptr;
    if(dev.codec_if) mics=esp_codec_dev_new(&dev);
    esp_codec_dev_sample_info_t format{}; format.sample_rate=16000; format.bits_per_sample=16; format.channel=2;
    speaker_ok=speaker && esp_codec_dev_open(speaker,&format)==ESP_CODEC_DEV_OK;
    if(speaker_ok) { esp_codec_dev_set_out_vol(speaker,20); esp_codec_dev_set_out_mute(speaker,true); }
    mics_ok=mics && esp_codec_dev_open(mics,&format)==ESP_CODEC_DEV_OK;
    if(mics_ok) mics_ok=esp_codec_dev_set_in_gain(mics,24)==ESP_CODEC_DEV_OK;
}
void audio_poll() {
    if(!mics_ok) return;
    int16_t pcm[512]; size_t bytes=0;
    stream_error=i2s_channel_read(rx,pcm,sizeof(pcm),&bytes,50);
    if(stream_error!=ESP_OK || bytes==0 || bytes%4) return;
    size_t count=bytes/4;
    for(int channel=0;channel<2;channel++) {
        double sum=0,squared=0; peak[channel]=0; clipped[channel]=0;
        for(size_t i=0;i<count;i++) { int sample=pcm[2*i+channel]; sum+=sample; squared+=double(sample)*sample;
            int magnitude=std::abs(sample); if(magnitude>peak[channel]) peak[channel]=magnitude; if(magnitude>=32760) clipped[channel]++; }
        dc[channel]=sum/count; rms[channel]=std::sqrt(std::fmax(0.0,squared/count-dc[channel]*dc[channel]));
    }
    captured+=count; observed=esp_timer_get_time()/1000;
}
bool audio_tone() {
    if(!speaker_ok || esp_codec_dev_set_out_mute(speaker,false)!=ESP_CODEC_DEV_OK) return false;
    bool ok=true; int16_t pcm[256*2];
    for(int block=0;block<16;block++) {
        for(int i=0;i<256;i++) { int n=block*256+i; double envelope=std::fmin(1.0,std::fmin(n/320.0,(4095-n)/320.0));
            pcm[2*i]=pcm[2*i+1]=static_cast<int16_t>(1800*envelope*std::sin(2*3.141592653589793*660*n/16000)); }
        size_t written=0; auto e=i2s_channel_write(tx,pcm,sizeof(pcm),&written,100);
        if(e!=ESP_OK || written!=sizeof(pcm)) { ok=false; break; }
    }
    esp_codec_dev_set_out_mute(speaker,true); return ok;
}
void audio_json(cJSON* root) {
    auto* j=cJSON_AddObjectToObject(root,"audio");
    cJSON_AddStringToObject(j,"speaker_codec",speaker_ok?"PASS":"FAIL");
    cJSON_AddStringToObject(j,"audible_acceptance","PENDING");
    cJSON_AddStringToObject(j,"microphone_codec",mics_ok?"PASS":"FAIL");
    cJSON_AddStringToObject(j,"capture",stream_error==ESP_OK && captured?"PASS":"PENDING");
    cJSON_AddStringToObject(j,"signal_variation",rms[0]>0 && rms[1]>0?"OBSERVED":"PENDING");
    cJSON_AddStringToObject(j,"capture_error",esp_err_to_name(stream_error));
    cJSON_AddStringToObject(j,"selected_inputs","MIC1,MIC2; physical slot orientation needs manual check");
    cJSON_AddNumberToObject(j,"samples_per_channel",captured); cJSON_AddNumberToObject(j,"observed_at_ms",observed);
    cJSON_AddItemToObject(j,"rms",cJSON_CreateDoubleArray(rms,2)); cJSON_AddItemToObject(j,"dc",cJSON_CreateDoubleArray(dc,2));
    cJSON_AddItemToObject(j,"peak",cJSON_CreateIntArray(peak,2)); cJSON_AddItemToObject(j,"clipped_samples",cJSON_CreateIntArray(clipped,2));
}

bool audio_ready() { return mics_ok && captured && stream_error==ESP_OK; }
double audio_level(int channel) { return channel>=0 && channel<2?rms[channel]:0; }
