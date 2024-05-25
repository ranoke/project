#include <string.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <esp_log.h>
#include <esp_eth.h>
#include <mqtt_client.h>
#include <driver/gpio.h>
#include <driver/adc.h>
#include <esp_netif.h>
#include <esp_event.h>
#include <esp_adc/adc_oneshot.h>

#define DEVICE_ID "123"
#define MQTT_BROKER "mqtt://192.168.1.100"
#define TOPIC_STATUS  "device/" DEVICE_ID "/status"
#define TOPIC_COMMAND "device/" DEVICE_ID "/command"

#define DEVICE_STATUS_PIN GPIO_NUM_2
#define DEVICE_POWER_PIN ADC1_CHANNEL_0

#define __MAYBE_UNUSED__ __attribute__((unused))

static esp_mqtt_client_handle_t client = NULL;
static adc_oneshot_unit_handle_t adc_unit_handle;

bool read_device_status() {
    return gpio_get_level(DEVICE_STATUS_PIN) == 1;
}

int write_device_status(bool power_on) {
    gpio_set_level(DEVICE_STATUS_PIN, power_on ? 1 : 0);
    return 0;
}

float read_device_power_consumption() {
    float raw;
    adc_oneshot_read(adc_unit_handle, DEVICE_POWER_PIN, &raw);
    return raw;
}

void gpio_init() {
    gpio_reset_pin(DEVICE_STATUS_PIN);
    gpio_set_direction(DEVICE_STATUS_PIN, GPIO_MODE_INPUT_OUTPUT);
    gpio_set_level(DEVICE_STATUS_PIN, 0); // Initialize to low
}

void adc_init() {
    adc_oneshot_chan_cfg_t chan_cfg = {
        .bitwidth = ADC_BITWIDTH_DEFAULT,
        .atten = ADC_ATTEN_DB_0
    };
    adc_oneshot_new_unit(ADC_UNIT_1, &adc_unit_handle);
    adc_oneshot_config_channel(adc_unit_handle, DEVICE_POWER_PIN, &chan_cfg);
}

void eth_init() {
    esp_netif_init();
    esp_netif_config_t cfg = ESP_NETIF_DEFAULT_ETH();
    __MAYBE_UNUSED__ esp_netif_t *eth_netif = esp_netif_new(&cfg);

    eth_mac_config_t mac_config = ETH_MAC_DEFAULT_CONFIG();
    eth_phy_config_t phy_config = ETH_PHY_DEFAULT_CONFIG();
    phy_config.phy_addr = 0;
    phy_config.reset_gpio_num = -1;

    esp_eth_mac_t *mac = esp_eth_mac_new_esp32((eth_esp32_emac_config_t*)&mac_config, &mac_config);
    esp_eth_phy_t *phy = esp_eth_phy_new_ip101(&phy_config);
    esp_eth_config_t config = ETH_DEFAULT_CONFIG(mac, phy);
    esp_eth_handle_t eth_handle = NULL;
    ESP_ERROR_CHECK(esp_eth_driver_install(&config, &eth_handle));
    ESP_ERROR_CHECK(esp_eth_start(eth_handle));
}

static void mqtt_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data) {
    esp_mqtt_event_handle_t event = event_data;
    switch (event->event_id) {
        case MQTT_EVENT_CONNECTED:
            esp_mqtt_client_subscribe(client, TOPIC_COMMAND, 0);
            break;
        case MQTT_EVENT_DATA:
            if (strcmp(event->topic, TOPIC_COMMAND) == 0) {
                bool power_on = strcmp("status_power_on:true", event->data) == 0;
                write_device_status(power_on);
            }
            break;
        default:
            break;
    }
}

static void mqtt_app_start(void) {
    const esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = MQTT_BROKER, // "mqtt://192.168.1.100:1883" directly in the URI
    };
    client = esp_mqtt_client_init(&mqtt_cfg);
    esp_mqtt_client_register_event(client, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(client);
}

static void report_device_status(void *pvParameters) {
    while (1) {
        bool device_status = read_device_status();
        float power_consumption = read_device_power_consumption();
        char message[128];
        sprintf(message, "{\"status\": \"%s\", \"power_usage\": %f}", device_status ? "on" : "off", power_consumption);
        esp_mqtt_client_publish(client, TOPIC_STATUS, message, 0, 1, 0);
        vTaskDelay(pdMS_TO_TICKS(5000));
    }
}

void app_main() {
    gpio_init();
    adc_init();
    eth_init();
    mqtt_app_start();
    xTaskCreate(report_device_status, "report_device_status", 4096, NULL, 5, NULL);
}